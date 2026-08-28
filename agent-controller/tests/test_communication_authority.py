import pytest
from zb_communication_orchestrator.authority import AuthorityError, Transition, derive_next_transition, load_transport_registry, validate_transition
class GH:
    def read_protected_file(self,path): assert path=='.github/zb/roles.yml'; return '{"approvedTransportActors":["Lester-Sparx"],"logicalRoles":["OWNER","LESTER","DUNCAN","DJANGO","JINGO"]}', 'blob'
def test_registry_separates_transport_from_logical_roles():
    r=load_transport_registry(GH()); assert r.approved_transport_actors==('Lester-Sparx',); assert 'DUNCAN' in r.logical_roles
def test_exact_transition_is_required(message):
    validate_transition(message,Transition('JINGO','LESTER','ASSIGN'))
    with pytest.raises(AuthorityError) as e: validate_transition(message,Transition('JINGO','DUNCAN','QC_REQUEST'))
    assert e.value.code=='ROLE_TRANSITION_ILLEGAL'
def test_flow_requires_duncan_and_conditional_django():
    assert derive_next_transition('RETURN',False)==Transition('JINGO','DUNCAN','QC_REQUEST')
    assert derive_next_transition('QC_VERDICT',False)==Transition('JINGO','JINGO','CLOSE_REQUEST')
    assert derive_next_transition('QC_VERDICT',True)==Transition('JINGO','DJANGO','ARCH_REVIEW')
    assert derive_next_transition('ARCH_VERDICT',True)==Transition('JINGO','JINGO','CLOSE_REQUEST')
def test_owner_boundary_stops():
    with pytest.raises(AuthorityError) as e: derive_next_transition('CLOSE_REQUEST',False)
    assert e.value.code=='OWNER_GATE_REQUIRED'
