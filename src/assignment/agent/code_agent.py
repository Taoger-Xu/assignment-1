"""The Part 1 coding agent: fix a software issue and submit a git patch."""

from __future__ import annotations

import json
from typing import Any

from assignment.agent.base import (
    DEFAULT_COMPACTION_KEEP_RECENT_STEPS,
    DEFAULT_COMPACTION_MAX_TOKENS,
    Agent,
    format_tool_output,
)
from assignment.agent.tools import EXECUTE_TOOL, SEND_MESSAGE_TOOL
from assignment.env import Environment

class CodeAgent(Agent):
    """An agent that fixes a software issue and submits a git patch."""

    def __init__(
        self,
        task: str,
        environment: Environment,
        model: str | None = None,
        logs_save_path: str | None = None,
        step_limit: int = 100,
        skills_path: str | None = None,
        auto_stop_environment: bool = True,
        compact_threshold_tokens: int | None = None,
        compaction_keep_recent_steps: int = DEFAULT_COMPACTION_KEEP_RECENT_STEPS,
        compaction_max_tokens: int = DEFAULT_COMPACTION_MAX_TOKENS,
    ):
        super().__init__(
            environment=environment,
            model=model,
            logs_save_path=logs_save_path,
            step_limit=step_limit,
            skills_path=skills_path,
            auto_stop_environment=auto_stop_environment,
            compact_threshold_tokens=compact_threshold_tokens,
            compaction_keep_recent_steps=compaction_keep_recent_steps,
            compaction_max_tokens=compaction_max_tokens,
        )
        self.task = task
        self.submitted_patch = ""

        # TODO(Part 1.3): Make the `execute` and `send_message` tools available
        # to the agent.
        self.tools.extend(
            [
                EXECUTE_TOOL,
                SEND_MESSAGE_TOOL,
            ]
        )

        # TODO(1.1.b): Construct the system prompt and task_prompt. These
        # should be usable by the `Agent.build_prompt` method.
        system_information = {
            "machine": self.env.machine,
            "release": self.env.release,
            "system": self.env.system,
            "version": self.env.version,
        }

        self.system_prompt = (
            "You are a software engineering agent working in a terminal "
            "environment. Investigate the task carefully, inspect the relevant "
            "source code, reproduce the problem when possible, make the smallest "
            "appropriate fix, and run relevant tests to verify the result. "
            "Use the available tools to interact with the environment. Inspect "
            "tool results and exit codes instead of assuming that a command "
            "succeeded.\n\n"
            "<system_information>\n"
            f"{json.dumps(system_information, indent=2)}\n"
            "</system_information>"
        )
        self.task_prompt = self.task
        # TODO(1.4): If any skills are available to the agent, make their
        # descriptions/metadata available to the agent in the prompt.
        if self.skills:
            skill_catalog = "\n\n".join(
                skill["metadata"] for skill in self.skills.values()
            )
            self.system_prompt += (
                "\n\n<available_skills>\n"
                "The following skills are available. Call invoke_skill with "
                "a skill name to read its complete instructions before using it.\n\n"
                f"{skill_catalog}\n"
                "</available_skills>"
            )

    def execute_tool_calls(
        self, tool_calls: list[dict[str, Any]]
    ) -> list[dict[str, str]]:
        """Execute ``execute`` and ``send_message`` calls in the code sandbox."""

        # TODO(Part 1.3): Parse each call, execute recognized tools, and return
        # one message per call (there may be multiple tool calls in one agent
        # response!). Malformed JSON and unknown tools must become recoverable
        # observations relayed to the agent instead of exceptions.
        observations: list[dict[str, str]] = []

        def observe(call_id: str, content: str) -> None:
            observations.append(
                {
                    "role": "tool",
                    "tool_call_id": call_id,
                    "content": content,
                }
            )

        for tool_call in tool_calls:
            if not isinstance(tool_call, dict):
                observe("", "Error: tool call must be an object.")
                continue

            raw_call_id = tool_call.get("id", "")
            call_id = raw_call_id if isinstance(raw_call_id, str) else str(raw_call_id)
            function = tool_call.get("function")
            if not isinstance(function, dict):
                observe(call_id, "Error: tool call function must be an object.")
                continue

            tool_name = function.get("name")
            raw_arguments = function.get("arguments")
            if not isinstance(tool_name, str):
                observe(call_id, "Error: tool name must be a string.")
                continue
            if not isinstance(raw_arguments, str):
                observe(call_id, "Error: tool arguments must be a JSON string.")
                continue

            try:
                arguments = json.loads(raw_arguments)
            except json.JSONDecodeError as exc:
                observe(call_id, f"Error: malformed JSON arguments: {exc}")
                continue

            if not isinstance(arguments, dict):
                observe(call_id, "Error: tool arguments must decode to an object.")
                continue

            if tool_name == "execute":
                allowed = {"command", "shell", "cwd", "timeout", "env"}
                extra = sorted(set(arguments) - allowed)
                command = arguments.get("command")
                shell = arguments.get("shell", True)
                cwd = arguments.get("cwd")
                timeout = arguments.get("timeout")
                command_env = arguments.get("env")

                error: str | None = None
                if extra:
                    error = f"Error: unexpected execute arguments: {', '.join(extra)}"
                elif not isinstance(command, (str, list)):
                    error = "Error: execute requires command to be a string or list."
                elif isinstance(command, list) and not all(
                    isinstance(item, str) for item in command
                ):
                    error = "Error: every item in command must be a string."
                elif shell is not None and not isinstance(shell, bool):
                    error = "Error: execute shell must be a boolean or null."
                elif cwd is not None and not isinstance(cwd, str):
                    error = "Error: execute cwd must be a string or null."
                elif timeout is not None and (
                    isinstance(timeout, bool)
                    or not isinstance(timeout, (int, float))
                ):
                    error = "Error: execute timeout must be a number or null."
                elif command_env is not None and (
                    not isinstance(command_env, dict)
                    or not all(
                        isinstance(key, str) and isinstance(value, str)
                        for key, value in command_env.items()
                    )
                ):
                    error = "Error: execute env must map strings to strings or be null."

                if error is not None:
                    observe(call_id, error)
                    continue

                try:
                    result = self.env.execute(
                        command=command,
                        shell=shell,
                        cwd=cwd,
                        timeout=timeout,
                        env=command_env,
                    )
                    content = format_tool_output(result)
                except Exception as exc:
                    content = f"Error executing tool: {type(exc).__name__}: {exc}"
                observe(call_id, content)

            elif tool_name == "invoke_skill":
                extra = sorted(set(arguments) - {"name"})
                name = arguments.get("name")
                if extra:
                    content = (
                        "Error: unexpected invoke_skill arguments: "
                        f"{', '.join(extra)}"
                    )
                elif not isinstance(name, str):
                    content = "Error: invoke_skill requires a string name."
                elif name not in self.skills:
                    content = f"Error: unknown skill: {name}"
                else:
                    content = self.skills[name]["content"]
                observe(call_id, content)

            elif tool_name == "send_message":
                extra = sorted(set(arguments) - {"summary"})
                summary = arguments.get("summary")
                if extra:
                    content = (
                        "Error: unexpected send_message arguments: "
                        f"{', '.join(extra)}"
                    )
                elif not isinstance(summary, str):
                    content = "Error: send_message requires a string summary."
                else:
                    self.finished = True
                    content = summary
                observe(call_id, content)

            else:
                observe(call_id, f"Error: unknown tool: {tool_name}")

        return observations
