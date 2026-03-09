from orion.core.protocol import parse_agent_output


def test_parse_agent_output_json_block():
    text = '```json\n{"response":"ok","tool":{"name":"web_search","args":{"query":"x"}}}\n```'
    decision = parse_agent_output(text)
    assert decision.response == "ok"
    assert decision.tool_name == "web_search"
    assert decision.tool_input == {"query": "x"}
