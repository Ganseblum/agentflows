import pathlib
import shutil
import subprocess
import sys
import tempfile

repo = pathlib.Path('/Users/lihanghang1/.codex/worktrees/l3-workflow-enhancement/agentflows')
cases = [
 ('report-uniqueness', 'skills/agentflow/scripts/workflow_lib/reports.py', [('    if len(set(names)) != len(names):', '    if False:')], ['test_workflow.WorkflowCliTests.test_duplicate_case_names_are_ambiguous']),
 ('source-scope', 'skills/agentflow/scripts/workflow_lib/snapshots.py', [('    if outside:\n', '    if False:\n')], ['test_workflow.WorkflowCliTests.test_untracked_out_of_scope_file_is_rejected', 'test_workflow.WorkflowCliTests.test_ignored_input_change_is_not_invisible']),
 ('managed-staleness', 'skills/agentflow/scripts/workflow_lib/managed.py', [('    if _state(target) != bundle["expected"]:', '    if False:'), ('        if _state(target) != bundle["expected"]:', '        if False:')], ['test_workflow.WorkflowCliTests.test_managed_preview_cannot_overwrite_later_user_change']),
 ('evidence-layout', 'tools/lab/gate/workspace.py', [('                    if n >= 5 and under[3] in ("evidence", "scratch"):', '                    if n == 5 and under[3] in ("evidence", "scratch"):')], ['test_workflow.EvidenceLayoutTests'])
]
with tempfile.TemporaryDirectory(prefix='agentflow-review-mutants-', dir='/tmp') as d:
 for name, rel, replacements, tests in cases:
  target = pathlib.Path(d)/name
  target.mkdir()
  for part in ('skills', 'tools', 'tests'):
   shutil.copytree(repo/part, target/part, ignore=shutil.ignore_patterns('__pycache__'))
  p = target/rel
  text = p.read_text()
  for old, new in replacements:
   rows = text.splitlines(keepends=True)
   hits = [i for i, row in enumerate(rows) if row.rstrip('\n') == old.rstrip('\n')]
   if len(hits) != 1:
    raise AssertionError((name, old, len(hits)))
   rows[hits[0]] = new.rstrip('\n')+'\n'
   text = ''.join(rows)
  p.write_text(text)
  argv = [sys.executable, '-m', 'unittest', *tests]
  print('MUTANT', name, 'COMMAND', repr(argv), flush=True)
  r = subprocess.run(argv, cwd=target/'tests', text=True, capture_output=True)
  print(r.stdout+r.stderr+'\nEXIT_CODE='+str(r.returncode), flush=True)
  if r.returncode != 1 or 'FAIL:' not in r.stderr or 'ERROR:' in r.stderr:
   raise AssertionError('Expected assertion failures only')
print('ALL_FOUR_MUTANTS_KILLED', flush=True)
