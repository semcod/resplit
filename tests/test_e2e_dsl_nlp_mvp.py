"""
E2E tests for DSL, NLP, and MVP protocol functionality.
"""
from pathlib import Path
import json
import time
import subprocess
import sys


def test_dsl_parsing():
    """Test DSL parsing and interpretation."""
    from rebuild.domain.dsl import DSLParser, DSLInterpreter

    parser = DSLParser()
    interpreter = DSLInterpreter()

    # Test walk command
    cmd = parser.parse("walk repo:/home/tom/github/maskservice/c2004 days:1 deploy:none")
    assert cmd.command.value == "walk"
    assert cmd.parameters["repo"] == "/home/tom/github/maskservice/c2004"
    assert cmd.parameters["days"] == 1
    assert cmd.parameters["deploy"] == "none"

    result = interpreter.execute(cmd)
    assert result["status"] == "parsed"
    assert result["repo"] == "/home/tom/github/maskservice/c2004"
    assert result["days"] == 1

    print("✓ DSL parsing test passed")


def test_dsl_file():
    """Test DSL file parsing."""
    from rebuild.domain.dsl import DSLParser, DSLInterpreter

    # Create a test DSL file
    test_file = Path("/tmp/test.dsl")
    test_file.write_text("""
# Test DSL script
walk repo:/home/tom/github/maskservice/c2004 days:1 deploy:none
analyze repo:/home/tom/github/semcod/resplit/rebuild type:duplicates min-lines:4
evolution timeline:/tmp/test_timeline.json output:/tmp/test_evolution.html
""")

    parser = DSLParser()
    interpreter = DSLInterpreter()

    commands = parser.parse_file(test_file)
    assert len(commands) == 3

    results = []
    for cmd in commands:
        result = interpreter.execute(cmd)
        results.append(result)

    assert all(r["status"] == "parsed" for r in results)
    test_file.unlink()

    print("✓ DSL file parsing test passed")


def test_nlp_parsing():
    """Test NLP natural language parsing."""
    from rebuild.application.services.nlp_service import NLPService

    nlp = NLPService()

    # Test analyze command
    cmd = nlp.parse("analyze code for duplicates")
    assert cmd.intent.value == "analyze"
    assert "type" in cmd.parameters
    assert cmd.confidence > 0

    dsl = nlp.to_dsl(cmd)
    assert "analyze" in dsl

    cli_args = nlp.to_cli_args(cmd)
    assert "analyze" in cli_args

    print("✓ NLP parsing test passed")


def test_nlp_various_commands():
    """Test NLP parsing for various command types."""
    from rebuild.application.services.nlp_service import NLPService

    nlp = NLPService()

    test_cases = [
        ("walk last 7 days", "walk"),
        ("analyze code for duplicates", "analyze"),
        ("generate evolution timeline", "evolution"),
        ("create PR with analysis", "auto_pr"),
    ]

    for text, expected_intent in test_cases:
        cmd = nlp.parse(text)
        assert cmd.intent.value == expected_intent, f"Expected {expected_intent}, got {cmd.intent.value}"
        print(f"  ✓ '{text}' -> {cmd.intent.value}")

    print("✓ NLP various commands test passed")


def test_mvp_protocol():
    """Test MVP protocol message handling."""
    from rebuild.domain.mvp_protocol import MVPMessage, MVPProtocolHandler, MessageType

    handler = MVPProtocolHandler()

    # Test DSL command via MVP
    msg = MVPMessage(
        message_type=MessageType.COMMAND,
        payload={
            "command": "dsl",
            "parameters": {"dsl": "walk repo:/home/tom/github/maskservice/c2004 days:1"}
        }
    )
    response = handler.handle_message(msg)
    assert response.message_type == MessageType.RESPONSE
    assert response.payload["status"] == "executed"

    # Test NLP command via MVP
    msg2 = MVPMessage(
        message_type=MessageType.COMMAND,
        payload={
            "command": "nlp",
            "parameters": {"text": "analyze code for duplicates"}
        }
    )
    response2 = handler.handle_message(msg2)
    assert response2.message_type == MessageType.RESPONSE
    assert response2.payload["status"] == "parsed"
    assert "intent" in response2.payload

    print("✓ MVP protocol test passed")


def test_mvp_json_serialization():
    """Test MVP message JSON serialization."""
    from rebuild.domain.mvp_protocol import MVPMessage, MessageType

    msg = MVPMessage(
        message_type=MessageType.COMMAND,
        payload={"command": "walk", "parameters": {"days": 7}}
    )

    json_str = msg.to_json()
    assert "version" in json_str
    assert "type" in json_str

    parsed = MVPMessage.from_json(json_str)
    assert parsed.message_type == MessageType.COMMAND
    assert parsed.payload["command"] == "walk"

    print("✓ MVP JSON serialization test passed")


def test_cli_dsl_command():
    """Test DSL CLI command."""
    result = subprocess.run(
        [sys.executable, "-m", "rebuild", "dsl", "--command", "walk repo:/home/tom/github/maskservice/c2004 days:1"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "walk" in result.stdout
    assert "Parameters:" in result.stdout

    print("✓ CLI DSL command test passed")


def test_cli_nlp_command():
    """Test NLP CLI command."""
    result = subprocess.run(
        [sys.executable, "-m", "rebuild", "nlp", "analyze code for duplicates", "--to-dsl"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "analyze" in result.stdout
    assert "DSL:" in result.stdout

    print("✓ CLI NLP command test passed")


def run_all_e2e_tests():
    """Run all E2E tests."""
    print("=" * 60)
    print("E2E Tests for DSL, NLP, and MVP Protocol")
    print("=" * 60)

    test_dsl_parsing()
    test_dsl_file()
    test_nlp_parsing()
    test_nlp_various_commands()
    test_mvp_protocol()
    test_mvp_json_serialization()
    test_cli_dsl_command()
    test_cli_nlp_command()

    print("=" * 60)
    print("All E2E tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    run_all_e2e_tests()
