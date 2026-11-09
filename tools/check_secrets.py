# -*- coding: utf-8 -*-
"""信息安全闸门：扫敏感串 / 敏感文件名 / 大文件。装成 pre-commit 就会一直拦。

用法：
    python tools/check_secrets.py            # 扫全部被跟踪的文件
    python tools/check_secrets.py --staged    # 只扫暂存区（pre-commit 用）
    python tools/check_secrets.py --history   # 额外扫全部历史（推之前跑一次）

退出码：0 = 干净；1 = 有命中（阻止提交）。
只用标准库，随包 runtime / 系统 python 都能跑。
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 本机用户名不写进仓库（写死等于自己把用户名公开出去）；
# 规则改成通用的「绝对路径里的 Users\<名字>」，历史探针在运行时按环境变量拼
_LOCAL_USERS = [u for u in (os.environ.get("USERNAME"), os.environ.get("USER")) if u]

# 内容规则：名字 → 正则
RULES = [
    ("微博/微信会话 token", re.compile(r"user_token\s*=")),
    ("微信 skey", re.compile(r"skey\s*=|@crypt_")),
    ("通用 token", re.compile(r"(access_token|refresh_token|bearer\s+[A-Za-z0-9._-]{20,})",
                              re.I)),
    ("私钥", re.compile(r"BEGIN (RSA |EC |OPENSSH |PGP )?PRIVATE KEY")),
    ("口令/密钥赋值", re.compile(r"(password|passwd|secret|api[_-]?key)\s*[=:]\s*['\"][^'\"]{6,}",
                                re.I)),
    ("本机用户目录绝对路径", re.compile(r"[A-Za-z]:[\\/]+Users[\\/]+[^\\/\s\"']+")),
    ("工作区绝对路径", re.compile(r"[A-Za-z]:[\\/]+entertain[\\/]+tmp")),
]

# 文件名规则（正则，匹配忽略大小写）
BAD_NAMES = [
    re.compile(r"(^|/)\.env($|\.)"),
    re.compile(r"\.(pem|pfx|p12|key|keystore|jks)$"),
    re.compile(r"(^|/)id_(rsa|ed25519)$"),
    re.compile(r"(^|/)_edge_profile/"),
    re.compile(r"(^|/)(cookies?|credential)s?\.(txt|json|dat)$"),
    re.compile(r"wb_snapshot\.html$"),      # 微博页面快照：正文用 .md 摘录代替
]

BIG = 3 * 1024 * 1024     # 单个文件 >3MB 提示（不是错误）
TEXT_EXT = (".py", ".md", ".json", ".txt", ".csv", ".html", ".js", ".yml", ".yaml",
            ".gitignore", ".sh", ".bat", ".spec", ".cfg", ".ini")


def sh(*args):
    r = subprocess.run(args, cwd=ROOT, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return r.stdout or ""


def files_all():
    return [x for x in sh("git", "ls-files").splitlines() if x.strip()]


def files_staged():
    out = sh("git", "diff", "--cached", "--name-only", "--diff-filter=ACMR")
    return [x for x in out.splitlines() if x.strip()]


def content_of(path, staged):
    if staged:
        r = subprocess.run(["git", "show", ":" + path], cwd=ROOT, capture_output=True)
        return r.stdout.decode("utf-8", "replace") if r.returncode == 0 else ""
    p = os.path.join(ROOT, path)
    if not os.path.isfile(p):
        return ""
    with open(p, "rb") as fh:
        return fh.read().decode("utf-8", "replace")


def scan(files, staged):
    hits, big = [], []
    self_files = {"tools/check_secrets.py", ".githooks/pre-commit"}   # 检查器自己含规则字面量
    for f in files:
        low = f.replace("\\", "/")
        if low in self_files:
            continue
        for rx in BAD_NAMES:
            if rx.search(low):
                hits.append((f, 0, "文件名命中：%s" % rx.pattern))
                break
        p = os.path.join(ROOT, f)
        if os.path.isfile(p) and os.path.getsize(p) > BIG:
            big.append((f, os.path.getsize(p)))
        if not low.lower().endswith(TEXT_EXT):
            continue
        text = content_of(f, staged)
        if not text:
            continue
        for name, rx in RULES:
            for m in rx.finditer(text):
                line = text[:m.start()].count("\n") + 1
                hits.append((f, line, "%s：%s" % (name, m.group(0)[:60])))
                break
    return hits, big


def scan_history():
    """推之前跑：历史里出现过的敏感串/文件名。"""
    bad = []
    probes = ["user_token=[A-Za-z0-9]", "skey=@crypt",
              "BEGIN OPENSSH PRIVATE KEY", "@crypt_"]
    probes += ["Users\\" + u for u in _LOCAL_USERS] + ["Users/" + u for u in _LOCAL_USERS]
    # 排除检查器自身（它必然含这些字面量），否则永远报自己
    skip = [":(exclude)tools/check_secrets.py", ":(exclude).githooks/pre-commit"]
    for probe in probes:
        out = sh("git", "log", "--oneline", "-S", probe, "--all", "--", ".", *skip)
        if out.strip():
            bad.append((probe, out.strip().splitlines()[:3]))
    names = sh("git", "log", "--name-only", "--pretty=format:").splitlines()
    for f in set(names):
        low = f.replace("\\", "/")
        for rx in BAD_NAMES:
            if rx.search(low):
                bad.append(("文件名", [f]))
                break
    return bad


def main():
    staged = "--staged" in sys.argv
    files = files_staged() if staged else files_all()
    hits, big = scan(files, staged)

    print("扫描 %d 个文件（%s）" % (len(files), "暂存区" if staged else "全部已跟踪"))
    if hits:
        print("\n!! 发现 %d 处敏感内容：" % len(hits))
        for f, line, msg in hits[:40]:
            print("   %s:%s  %s" % (f, line, msg))
        print("\n修法：删掉/改成占位符；确属需要的素材（如页面快照）改存正文摘录 .md。")
    if big:
        print("\n提示：以下文件 >3MB（打包产物别入库）：")
        for f, s in big[:10]:
            print("   %.1f MB  %s" % (s / 1048576.0, f))

    if "--history" in sys.argv:
        bad = scan_history()
        if bad:
            print("\n!! 历史里也有（推送前会公开）：")
            for name, lines in bad:
                print("   [%s] %s" % (name, "; ".join(lines)))
            hits = hits or [("history", 0, "历史含敏感内容")]

    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
