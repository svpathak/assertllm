
PROMPT_TEMPLATE = """\
Here is an API response:
<response>
{response}
</response>

Evaluate each assertion below. Answer YES or NO for each, in the same order.

{assertions}

Reply in this exact format:
{format}"""

class JudgeUtils:

    @staticmethod
    def build_prompt(response: str, assertions: list[str]) -> str:
        numbered = "\n".join(f"{i + 1}. {a}" for i, a in enumerate(assertions))
        fmt = "\n".join(f"{i + 1}. YES or NO" for i in range(len(assertions)))
        return PROMPT_TEMPLATE.format(response=response, assertions=numbered, format=fmt)

    @staticmethod
    def parse_response(text: str, count: int) -> list[bool]:
        results = []
        for line in text.strip().splitlines():
            line = line.strip()
            if not line:
                continue
            upper = line.upper()
            if "YES" in upper:
                results.append(True)
            elif "NO" in upper:
                results.append(False)
        if len(results) != count:
            raise ValueError(f"Expected {count} judgments, got {len(results)}")
        return results