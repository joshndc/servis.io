from services.rules import match_rule

def test_exact_keyword_match():
    rules = [{"keyword": "price", "reply_template": "Our prices start at ₱80."}]
    assert match_rule("what is your price", rules) == "Our prices start at ₱80."

def test_case_insensitive_match():
    rules = [{"keyword": "MENU", "reply_template": "Here is our menu!"}]
    assert match_rule("Can I see the menu?", rules) == "Here is our menu!"

def test_no_match_returns_none():
    rules = [{"keyword": "price", "reply_template": "₱80"}]
    assert match_rule("hello", rules) is None

def test_empty_rules_returns_none():
    assert match_rule("hello", []) is None

def test_first_matching_rule_wins():
    rules = [
        {"keyword": "price", "reply_template": "First"},
        {"keyword": "price", "reply_template": "Second"},
    ]
    assert match_rule("price?", rules) == "First"
