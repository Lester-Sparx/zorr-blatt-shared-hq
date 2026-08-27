from __future__ import annotations
from dataclasses import dataclass
import json, subprocess
from typing import Any, Callable
from zb_local_controller.task_contract import TaskContractError, parse_task

class BridgeGitHubError(RuntimeError):
    def __init__(self, code: str): self.code=code; super().__init__(code)

@dataclass(frozen=True)
class BridgeIssue:
    number:int; title:str; body:str; comments:tuple[str,...]

class BridgeGitHubCLI:
    def __init__(self, repository:str, runner:Callable[...,Any]=subprocess.run): self.repository=repository; self.runner=runner
    def _run(self,args:list[str],code:str):
        try: r=self.runner(args,capture_output=True,text=True,shell=False)
        except Exception as exc: raise BridgeGitHubError(code) from exc
        if getattr(r,'returncode',1)!=0: raise BridgeGitHubError(code)
        return r
    def ensure_authenticated(self)->None: self._run(['gh','auth','status'],'BRIDGE_GH_AUTH_FAILED')
    def list_task_issues(self)->tuple[BridgeIssue,...]:
        r=self._run(['gh','issue','list','--repo',self.repository,'--state','open','--search','ZB_AGENT_TASK_V0','--limit','1000','--json','number,title,body,comments'],'BRIDGE_GH_ISSUE_LIST_FAILED')
        try:
            rows=json.loads(r.stdout)
            if not isinstance(rows,list): raise ValueError
        except Exception as exc: raise BridgeGitHubError('BRIDGE_GH_OUTPUT_INVALID') from exc
        out=[]
        for row in rows:
            try:
                if not isinstance(row,dict): raise ValueError
                number=int(row['number']); title=str(row['title']); body=row['body']; cr=row.get('comments',[])
                if not isinstance(body,str) or not isinstance(cr,list): raise ValueError
                parse_task(body)
                comments=tuple(str(x['body']) for x in cr if isinstance(x,dict) and isinstance(x.get('body'),str))
            except TaskContractError: continue
            except Exception as exc: raise BridgeGitHubError('BRIDGE_GH_OUTPUT_INVALID') from exc
            out.append(BridgeIssue(number,title,body,comments))
        return tuple(out)
    def post_reference_event(self,issue_number:int,body:str)->None:
        self._run(['gh','issue','comment',str(int(issue_number)),'--repo',self.repository,'--body',body],'BRIDGE_GH_COMMENT_FAILED')
