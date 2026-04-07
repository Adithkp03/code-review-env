"""Problem dataset for the code review environment."""

PROBLEMS = [
    {
        "id": "off_by_one_loop",
        "difficulty": "easy",
        "flaw_type": "bug",
        "description": "Return the sum of all numbers in the input list.",
        "flawed_code": """def solution(nums):
    total = 0
    for i in range(len(nums) - 1):
        total += nums[i]
    return total
""",
        "correct_code": """def solution(nums):
    total = 0
    for value in nums:
        total += value
    return total
""",
        "test_cases": [
            {"input": {"nums": [1, 2, 3]}, "expected_output": 6, "description": "basic positive values"},
            {"input": {"nums": [5]}, "expected_output": 5, "description": "single element edge case"},
            {"input": {"nums": []}, "expected_output": 0, "description": "empty list edge case"},
        ],
        "hint": "Check the loop bounds carefully.",
        "flaw_explanation": "The loop stops one element early and misses the last list item due to an off by one range.",
    },
    {
        "id": "wrong_operator",
        "difficulty": "easy",
        "flaw_type": "bug",
        "description": "Return the sum of all numbers in the list.",
        "flawed_code": """def solution(nums):
    total = 0
    for n in nums:
        total -= n
    return total
""",
        "correct_code": """def solution(nums):
    total = 0
    for n in nums:
        total += n
    return total
""",
        "test_cases": [
            {"input": {"nums": [1, 2, 3]}, "expected_output": 6, "description": "normal case"},
            {"input": {"nums": [-1, 1]}, "expected_output": 0, "description": "mixed signs"},
            {"input": {"nums": []}, "expected_output": 0, "description": "empty list"},
        ],
        "hint": "Accumulator updates in the loop use the wrong arithmetic operator.",
        "flaw_explanation": "The function subtracts each number from total instead of adding, so it computes a negative sum.",
    },
    {
        "id": "missing_return",
        "difficulty": "easy",
        "flaw_type": "bug",
        "description": "Return 'adult' for age >= 18, otherwise return 'minor'.",
        "flawed_code": """def solution(age):
    if age >= 18:
        return "adult"
    else:
        status = "minor"
""",
        "correct_code": """def solution(age):
    if age >= 18:
        return "adult"
    return "minor"
""",
        "test_cases": [
            {"input": {"age": 20}, "expected_output": "adult", "description": "adult branch"},
            {"input": {"age": 10}, "expected_output": "minor", "description": "minor branch"},
            {"input": {"age": 18}, "expected_output": "adult", "description": "boundary condition"},
        ],
        "hint": "One branch computes a value but never returns it.",
        "flaw_explanation": "The else branch falls through without a return statement, causing None for minors.",
    },
    {
        "id": "mutable_default_arg",
        "difficulty": "medium",
        "flaw_type": "bug",
        "description": "Append a task string to a list and return the updated list.",
        "flawed_code": """def solution(task, tasks=[]):
    tasks.append(task)
    return tasks
""",
        "correct_code": """def solution(task, tasks=None):
    if tasks is None:
        tasks = []
    tasks.append(task)
    return tasks
""",
        "test_cases": [
            {"input": {"task": "a"}, "expected_output": ["a"], "description": "first call default list"},
            {"input": {"task": "b"}, "expected_output": ["b"], "description": "second call should be fresh list"},
            {"input": {"task": "x", "tasks": ["z"]}, "expected_output": ["z", "x"], "description": "explicit list argument"},
        ],
        "hint": "Default parameters are evaluated once in Python.",
        "flaw_explanation": "A mutable default list is shared across calls, so state leaks between invocations.",
    },
    {
        "id": "integer_division",
        "difficulty": "easy",
        "flaw_type": "bug",
        "description": "Return the average of two numbers as a float.",
        "flawed_code": """def solution(a, b):
    return (a + b) // 2
""",
        "correct_code": """def solution(a, b):
    return (a + b) / 2
""",
        "test_cases": [
            {"input": {"a": 1, "b": 2}, "expected_output": 1.5, "description": "odd total needs decimal"},
            {"input": {"a": 2, "b": 4}, "expected_output": 3.0, "description": "even total"},
            {"input": {"a": -1, "b": 0}, "expected_output": -0.5, "description": "negative value case"},
        ],
        "hint": "Integer floor behavior is dropping fractional precision.",
        "flaw_explanation": "The code uses floor division so decimal values are truncated instead of returning a true average.",
    },
    {
        "id": "reversed_condition",
        "difficulty": "easy",
        "flaw_type": "bug",
        "description": "Return True if current temperature is below threshold.",
        "flawed_code": """def solution(temp, threshold):
    return temp > threshold
""",
        "correct_code": """def solution(temp, threshold):
    return temp < threshold
""",
        "test_cases": [
            {"input": {"temp": 10, "threshold": 20}, "expected_output": True, "description": "below threshold"},
            {"input": {"temp": 20, "threshold": 20}, "expected_output": False, "description": "equal boundary"},
            {"input": {"temp": 30, "threshold": 20}, "expected_output": False, "description": "above threshold"},
        ],
        "hint": "The comparison direction is inverted.",
        "flaw_explanation": "The condition checks greater than instead of less than, reversing the intended logic.",
    },
    {
        "id": "infinite_loop_risk",
        "difficulty": "medium",
        "flaw_type": "bug",
        "description": "Count down from n to zero and return how many iterations were needed.",
        "flawed_code": """def solution(n):
    steps = 0
    while n > 0:
        n += 1
        steps += 1
    return steps
""",
        "correct_code": """def solution(n):
    steps = 0
    while n > 0:
        n -= 1
        steps += 1
    return steps
""",
        "test_cases": [
            {"input": {"n": 0}, "expected_output": 0, "description": "already zero"},
            {"input": {"n": 1}, "expected_output": 1, "description": "single loop iteration"},
            {"input": {"n": 3}, "expected_output": 3, "description": "multiple decrements"},
        ],
        "hint": "The loop variable changes in the wrong direction.",
        "flaw_explanation": "The loop increments n while checking n > 0, so positive inputs never terminate.",
    },
    {
        "id": "nested_loop_search",
        "difficulty": "medium",
        "flaw_type": "inefficiency",
        "description": "Return all items from list_a that also exist in list_b.",
        "flawed_code": """def solution(list_a, list_b):
    result = []
    for a in list_a:
        for b in list_b:
            if a == b:
                result.append(a)
                break
    return result
""",
        "correct_code": """def solution(list_a, list_b):
    lookup = set(list_b)
    result = []
    for a in list_a:
        if a in lookup:
            result.append(a)
    return result
""",
        "test_cases": [
            {"input": {"list_a": [1, 2, 3], "list_b": [2, 4]}, "expected_output": [2], "description": "single overlap"},
            {"input": {"list_a": [], "list_b": [1]}, "expected_output": [], "description": "empty first list"},
            {"input": {"list_a": [5, 5, 6], "list_b": [5]}, "expected_output": [5, 5], "description": "duplicates preserved"},
        ],
        "hint": "Repeated membership checks can be constant time with a better data structure.",
        "flaw_explanation": "The nested loops cause O(n squared) behavior; using a set for lookup reduces repeated scans.",
    },
    {
        "id": "repeated_computation",
        "difficulty": "easy",
        "flaw_type": "inefficiency",
        "description": "Return list of indices for the given list.",
        "flawed_code": """def solution(items):
    indices = []
    i = 0
    while i < len(items):
        indices.append(i)
        i += 1
    return indices
""",
        "correct_code": """def solution(items):
    indices = []
    n = len(items)
    i = 0
    while i < n:
        indices.append(i)
        i += 1
    return indices
""",
        "test_cases": [
            {"input": {"items": ["a", "b", "c"]}, "expected_output": [0, 1, 2], "description": "normal list"},
            {"input": {"items": []}, "expected_output": [], "description": "empty edge case"},
            {"input": {"items": [42]}, "expected_output": [0], "description": "single item"},
        ],
        "hint": "A value that does not change is recomputed each loop iteration.",
        "flaw_explanation": "Calling len repeatedly in the loop condition is unnecessary work; compute it once before looping.",
    },
    {
        "id": "string_concatenation",
        "difficulty": "medium",
        "flaw_type": "inefficiency",
        "description": "Join a list of words using commas.",
        "flawed_code": """def solution(words):
    out = ""
    for i, word in enumerate(words):
        if i > 0:
            out += ","
        out += word
    return out
""",
        "correct_code": """def solution(words):
    return ",".join(words)
""",
        "test_cases": [
            {"input": {"words": ["a", "b", "c"]}, "expected_output": "a,b,c", "description": "normal join"},
            {"input": {"words": []}, "expected_output": "", "description": "empty list"},
            {"input": {"words": ["single"]}, "expected_output": "single", "description": "single element"},
        ],
        "hint": "Repeated immutable string concatenation scales poorly.",
        "flaw_explanation": "Using plus equals in a loop creates many intermediate strings; join is the efficient pattern.",
    },
    {
        "id": "redundant_sort",
        "difficulty": "easy",
        "flaw_type": "inefficiency",
        "description": "Return a sorted copy of the input list in ascending order.",
        "flawed_code": """def solution(values):
    sorted_values = sorted(values)
    return sorted(sorted_values)
""",
        "correct_code": """def solution(values):
    return sorted(values)
""",
        "test_cases": [
            {"input": {"values": [3, 1, 2]}, "expected_output": [1, 2, 3], "description": "unsorted input"},
            {"input": {"values": []}, "expected_output": [], "description": "empty list"},
            {"input": {"values": [1, 1, 0]}, "expected_output": [0, 1, 1], "description": "duplicates"},
        ],
        "hint": "The output of one expensive operation is passed to the same operation again.",
        "flaw_explanation": "Sorting twice is redundant because one sort already produces the final ordered list.",
    },
    {
        "id": "unnecessary_list_copy",
        "difficulty": "easy",
        "flaw_type": "inefficiency",
        "description": "Return a list where each number is doubled.",
        "flawed_code": """def solution(nums):
    copied = nums[:]
    result = []
    for n in copied:
        result.append(n * 2)
    return result
""",
        "correct_code": """def solution(nums):
    result = []
    for n in nums:
        result.append(n * 2)
    return result
""",
        "test_cases": [
            {"input": {"nums": [1, 2, 3]}, "expected_output": [2, 4, 6], "description": "normal case"},
            {"input": {"nums": []}, "expected_output": [], "description": "empty list"},
            {"input": {"nums": [-1]}, "expected_output": [-2], "description": "negative number"},
        ],
        "hint": "A full shallow copy is made even though iteration is read-only.",
        "flaw_explanation": "Copying the list before a single pass wastes memory and time when the original list is not mutated.",
    },
    {
        "id": "sql_injection",
        "difficulty": "hard",
        "flaw_type": "security",
        "description": "Build a SQL query and parameters to fetch users by username safely.",
        "flawed_code": """def solution(username):
    query = f"SELECT * FROM users WHERE username = '{username}'"
    return query, None
""",
        "correct_code": """def solution(username):
    query = "SELECT * FROM users WHERE username = ?"
    return query, (username,)
""",
        "test_cases": [
            {"input": {"username": "alice"}, "expected_output": ("SELECT * FROM users WHERE username = ?", ("alice",)), "description": "normal username"},
            {"input": {"username": "a' OR 1=1 --"}, "expected_output": ("SELECT * FROM users WHERE username = ?", ("a' OR 1=1 --",)), "description": "injection payload stays as parameter"},
            {"input": {"username": ""}, "expected_output": ("SELECT * FROM users WHERE username = ?", ("",)), "description": "empty username"},
        ],
        "hint": "Do not interpolate untrusted input into SQL strings.",
        "flaw_explanation": "The query is built with string formatting, enabling injection; parameterized placeholders prevent that.",
    },
    {
        "id": "hardcoded_secret",
        "difficulty": "medium",
        "flaw_type": "security",
        "description": "Build an Authorization header using a provided API key argument.",
        "flawed_code": """def solution(api_key):
    key = "HARDCODED_SECRET_TOKEN"
    return {"Authorization": "Bearer " + key}
""",
        "correct_code": """def solution(api_key):
    return {"Authorization": "Bearer " + api_key}
""",
        "test_cases": [
            {"input": {"api_key": "k1"}, "expected_output": {"Authorization": "Bearer k1"}, "description": "normal key"},
            {"input": {"api_key": ""}, "expected_output": {"Authorization": "Bearer "}, "description": "empty key allowed"},
            {"input": {"api_key": "prod-123"}, "expected_output": {"Authorization": "Bearer prod-123"}, "description": "different key respected"},
        ],
        "hint": "Credentials should come from inputs or secure stores, not source literals.",
        "flaw_explanation": "A secret token is hardcoded, which leaks sensitive data and ignores the provided credential input.",
    },
    {
        "id": "eval_usage",
        "difficulty": "hard",
        "flaw_type": "security",
        "description": "Safely parse a JSON object string into a Python dictionary.",
        "flawed_code": """def solution(payload):
    return eval(payload)
""",
        "correct_code": """import json

def solution(payload):
    return json.loads(payload)
""",
        "test_cases": [
            {"input": {"payload": "{\"x\": 1}"}, "expected_output": {"x": 1}, "description": "simple object"},
            {"input": {"payload": "{\"ok\": true, \"n\": 2}"}, "expected_output": {"ok": True, "n": 2}, "description": "boolean support"},
            {"input": {"payload": "{}"}, "expected_output": {}, "description": "empty object"},
        ],
        "hint": "Use a parser for the expected data format instead of arbitrary code execution.",
        "flaw_explanation": "Evaluating user input executes arbitrary Python code; JSON decoding parses data without code execution.",
    },
    {
        "id": "path_traversal",
        "difficulty": "hard",
        "flaw_type": "security",
        "description": "Build a safe file path under /safe_base for a user-provided filename.",
        "flawed_code": """def solution(filename):
    return "/safe_base/" + filename
""",
        "correct_code": """def solution(filename):
    if "/" in filename or "\\\\" in filename or ".." in filename:
        raise ValueError("invalid filename")
    return "/safe_base/" + filename
""",
        "test_cases": [
            {"input": {"filename": "notes.txt"}, "expected_output": "/safe_base/notes.txt", "description": "valid file name"},
            {"input": {"filename": "a/b.txt"}, "expected_output": "ValueError", "description": "nested path rejected"},
            {"input": {"filename": "../secret.txt"}, "expected_output": "ValueError", "description": "parent traversal rejected"},
        ],
        "hint": "Reject separators and parent-directory tokens in user paths.",
        "flaw_explanation": "Unsanitized path input allows directory traversal; validating filename tokens prevents escaping the base directory.",
    },
    {
        "id": "god_function",
        "difficulty": "hard",
        "flaw_type": "style",
        "description": "Process sales values by validating input, filtering negatives, computing total, average, and max in a clean structure.",
        "flawed_code": """def solution(values):
    if not isinstance(values, list):
        raise TypeError("values must be a list")
    cleaned = []
    for v in values:
        if isinstance(v, (int, float)) and v >= 0:
            cleaned.append(v)
    total = 0
    for n in cleaned:
        total += n
    count = len(cleaned)
    avg = total / count if count > 0 else 0.0
    max_val = max(cleaned) if cleaned else 0
    report = {"count": count, "total": total, "average": avg, "max": max_val}
    return report
""",
        "correct_code": """def _validate(values):
    if not isinstance(values, list):
        raise TypeError("values must be a list")

def _clean(values):
    return [v for v in values if isinstance(v, (int, float)) and v >= 0]

def _summarize(cleaned):
    total = sum(cleaned)
    count = len(cleaned)
    average = total / count if count > 0 else 0.0
    max_value = max(cleaned) if cleaned else 0
    return {"count": count, "total": total, "average": average, "max": max_value}

def solution(values):
    _validate(values)
    cleaned = _clean(values)
    return _summarize(cleaned)
""",
        "test_cases": [
            {"input": {"values": [1, 2, -1, "x"]}, "expected_output": {"count": 2, "total": 3, "average": 1.5, "max": 2}, "description": "filters invalid and negative values"},
            {"input": {"values": []}, "expected_output": {"count": 0, "total": 0, "average": 0.0, "max": 0}, "description": "empty list"},
            {"input": {"values": [5]}, "expected_output": {"count": 1, "total": 5, "average": 5.0, "max": 5}, "description": "single value"},
        ],
        "hint": "Separate validation, transformation, and summarization responsibilities.",
        "flaw_explanation": "The function mixes many unrelated responsibilities in one block; decomposition improves readability and maintainability.",
    },
    {
        "id": "magic_numbers",
        "difficulty": "medium",
        "flaw_type": "style",
        "description": "Convert Celsius to Fahrenheit.",
        "flawed_code": """def solution(celsius):
    return celsius * 1.8 + 32
""",
        "correct_code": """MULTIPLIER = 9 / 5
FREEZING_OFFSET = 32

def solution(celsius):
    return celsius * MULTIPLIER + FREEZING_OFFSET
""",
        "test_cases": [
            {"input": {"celsius": 0}, "expected_output": 32.0, "description": "freezing point"},
            {"input": {"celsius": 100}, "expected_output": 212.0, "description": "boiling point"},
            {"input": {"celsius": -40}, "expected_output": -40.0, "description": "same in both scales"},
        ],
        "hint": "Numeric constants should explain themselves via names.",
        "flaw_explanation": "Hardcoded unexplained numeric literals reduce readability; named constants make intent clear.",
    },
    {
        "id": "poor_naming",
        "difficulty": "medium",
        "flaw_type": "style",
        "description": "Compute weighted average score from values and matching weights.",
        "flawed_code": """def solution(a, b):
    x = 0
    y = 0
    for i in range(len(a)):
        x += a[i] * b[i]
        y += b[i]
    if y == 0:
        return 0
    return x / y
""",
        "correct_code": """def solution(values, weights):
    weighted_sum = 0
    total_weight = 0
    for index in range(len(values)):
        weighted_sum += values[index] * weights[index]
        total_weight += weights[index]
    if total_weight == 0:
        return 0
    return weighted_sum / total_weight
""",
        "test_cases": [
            {"input": {"values": [10, 20], "weights": [1, 3]}, "expected_output": 17.5, "description": "basic weighted average"},
            {"input": {"values": [5], "weights": [0]}, "expected_output": 0, "description": "zero total weight"},
            {"input": {"values": [1, 2, 3], "weights": [1, 1, 1]}, "expected_output": 2.0, "description": "uniform weights"},
        ],
        "hint": "Rename short cryptic identifiers to descriptive names.",
        "flaw_explanation": "Single-letter variables in non-trivial logic harm clarity and make maintenance difficult.",
    },
    {
        "id": "no_error_handling",
        "difficulty": "medium",
        "flaw_type": "style",
        "description": "Parse an integer from a text value and return -1 when parsing fails.",
        "flawed_code": """def solution(text):
    return int(text.strip())
""",
        "correct_code": """def solution(text):
    try:
        return int(text.strip())
    except (ValueError, AttributeError):
        return -1
""",
        "test_cases": [
            {"input": {"text": "42"}, "expected_output": 42, "description": "valid integer"},
            {"input": {"text": " 7 "}, "expected_output": 7, "description": "surrounding spaces"},
            {"input": {"text": "abc"}, "expected_output": -1, "description": "invalid number edge case"},
        ],
        "hint": "External input parsing should fail gracefully.",
        "flaw_explanation": "The function performs risky parsing without exception handling, causing unhandled errors for bad input.",
    },
]
