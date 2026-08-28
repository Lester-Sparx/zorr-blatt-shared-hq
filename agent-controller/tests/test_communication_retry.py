import pytest
from zb_communication_orchestrator.retry import RetryError, RetryPolicy, retry_operation

def test_bounded_retry_succeeds_before_limit():
    seen=[]
    def f(attempt): seen.append(attempt); return 'ok' if attempt==3 else None
    assert retry_operation(RetryPolicy(3),f,is_success=bool)=='ok' and seen==[1,2,3]

def test_exhaustion_is_stable():
    with pytest.raises(RetryError) as e: retry_operation(RetryPolicy(2),lambda n:None,is_success=bool)
    assert e.value.code=='RETRY_EXHAUSTED'
