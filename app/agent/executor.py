import logging

from app.tools.base_tool import BaseTool

logger = logging.getLogger(__name__)


class Executor:
    """Executes a selected tool with given parameters."""

    def __init__(self, tools: list[BaseTool]):
        self._registry: dict[str, BaseTool] = {tool.name: tool for tool in tools}

    def run(self, tool_name: str, parameters: str) -> str:
        """Execute the named tool with the provided parameters.

        Returns the tool output string or an error message.
        """
        tool = self._registry.get(tool_name)
        if tool is None:
            available = ", ".join(self._registry.keys())
            msg = f"Tool '{tool_name}' not found. Available tools: {available}"
            logger.error(msg)
            return msg

        logger.info(f"Executing tool '{tool_name}' with input: {parameters}")
        try:
            result = tool.execute(parameters)
            logger.info(f"Tool '{tool_name}' result: {result}")
            return result
        except Exception as e:
            msg = f"Tool '{tool_name}' execution failed: {e}"
            logger.error(msg)
            return msg
