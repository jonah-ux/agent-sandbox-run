import argparse,json,subprocess,shlex,time,shutil

def main(argv=None):
 p=argparse.ArgumentParser(prog="agent-sandbox"); p.add_argument("command",choices=["run"]); p.add_argument("--root",default="."); p.add_argument("--timeout",type=int,default=10); p.add_argument("cmd",nargs=argparse.REMAINDER); a=p.parse_args(argv); cmd=a.cmd or ["/bin/echo","sandbox demo"]; started=time.time(); backend=shutil.which("bwrap"); enforced=bool(backend)
 if enforced: actual=[backend,"--ro-bind",a.root,"/workspace","--chdir","/workspace","--proc","/proc","--dev","/dev","--unshare-net","--"]+cmd
 else: actual=cmd
 try: r=subprocess.run(actual,text=True,capture_output=True,timeout=a.timeout); code=r.returncode; out=r.stdout; err=r.stderr
 except subprocess.TimeoutExpired as e: code=124; out=e.stdout or ""; err="timeout"
 receipt={"schema":"agent-sandbox/v1","ok":code==0,"exit_code":code,"backend":"bubblewrap" if enforced else "fallback","enforced":enforced,"duration_ms":round((time.time()-started)*1000),"stdout":out,"stderr":err}; print(json.dumps(receipt,indent=2)); return code
