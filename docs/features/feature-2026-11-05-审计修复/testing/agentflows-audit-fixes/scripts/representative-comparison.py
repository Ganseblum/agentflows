"""Matched 0.40/0.41 generation samples and CARD-1 red/green, outside real trees."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

def run(argv, cwd):
    started=time.monotonic()
    p=subprocess.run([str(v) for v in argv],cwd=cwd,capture_output=True,text=True,timeout=30)
    return {'argv':[str(v) for v in argv],'cwd':str(cwd),'exit':p.returncode,
            'stdout':p.stdout,'stderr':p.stderr,'duration_seconds':time.monotonic()-started}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, required=True, help='0.40-compatible frozen checkout')
    parser.add_argument('--baseline-revision', required=True, help='Revision of the supplied baseline tree')
    parser.add_argument('--source', type=Path, required=True, help='Current checkout or frozen candidate')
    parser.add_argument('--source-revision', required=True, help='Revision or freeze identity of the candidate')
    parser.add_argument('--output', type=Path, required=True, help='New JSON evidence file')
    args = parser.parse_args()
    baseline, source = args.baseline.resolve(), args.source.resolve()
    if baseline == source:
        parser.error('baseline and candidate must be different trees')
    for tree in (baseline, source):
        if not (tree / 'skills/agentflow/scripts/new_feature.py').is_file():
            parser.error(f'invalid Agentflow checkout: {tree}')
    if args.output.exists() or args.output.is_symlink():
        parser.error('choose a new --output file')
    results=[]
    with tempfile.TemporaryDirectory(prefix='af-representative-comparison-',dir='/tmp') as directory:
        root=Path(directory).resolve()
        for card,tier,tracks in [('CARD-1','light',[]),('CARD-2','light',[]),('CARD-3','full',['be','fe']),('CARD-4','full',['be','fe'])]:
            for label,source_root in [('old',baseline),('new',source)]:
                hub=root/(card+'-'+label);hub.mkdir()
                (hub/'index.md').write_text('| 批次 | 一句话范围 | 进度板 |\n| --- | --- | --- |\n')
                argv=[sys.executable,'-B',source_root/'skills/agentflow/scripts/new_feature.py','--hub',hub,'--slug',card.lower(),'--date','2026-11-05']
                if label=='new':
                    argv+=['--tier',tier]
                    if tracks:argv+=['--tracks',','.join(tracks)]
                command=run(argv,root)
                assert command['exit']==0,command
                feature=hub/'features'/('feature-2026-11-05-'+card.lower())
                files={p.relative_to(feature).as_posix() for p in feature.rglob('*') if p.is_file()}
                desired={'README.md'} if tier=='light' else {
                    'README.md','proposal/proposal.md','plan/execution.md','spec/checklist.md',
                    'spec/be/backend.md','design/be/backend.md','spec/fe/frontend.md','design/fe/frontend.md',
                    'spec/qa/acceptance.md','design/qa/testing.md'}
                first_pass=files==desired
                interventions=[]
                if label=='old':
                    # These are measured fixture normalization operations, not
                    # inferred human/model effort or production effectiveness.
                    if tier=='light':
                        shutil.copyfile(feature/'lightweight.md',feature/'README.md')
                        interventions.append('replace full README with shipped lightweight template')
                    for name in sorted(files-desired):
                        (feature/name).unlink();interventions.append('remove '+name)
                final={p.relative_to(feature).as_posix() for p in feature.rglob('*') if p.is_file()}
                assert final==desired,(card,label,final)
                results.append({'card':card,'version':label,'command':command,'initial_files':sorted(files),
                                'initial_count':len(files),'first_pass_material_shape':first_pass,
                                'fixture_normalization_operations':interventions,'normalization_count':len(interventions),
                                'final_files':sorted(final),'token_cost':'not reported','model_efficiency':'unverified'})
        small=root/'card1';small.mkdir()
        (small/'value.cjs').write_text("module.exports = value => { if (!Number.isFinite(value)) throw new TypeError('finite number required'); return Math.max(0,Math.min(10,value || 1)); };\n")
        tests="""const test=require('node:test');const assert=require('node:assert/strict');const clamp=require('./value.cjs');
for(const [input,expected] of [[0,0],[-1,0],[11,10],[5,5]])test('CARD-1 clamp '+input,()=>assert.equal(clamp(input),expected));
test('CARD-1 rejects invalid',()=>assert.throws(()=>clamp('not-number'),/finite number/));
"""
        (small/'value.test.cjs').write_text(tests)
        red=run(['node','--test','--test-reporter=tap','value.test.cjs'],small)
        assert red['exit']!=0 and 'not ok 1 - CARD-1 clamp 0' in red['stdout'],red
        (small/'value.cjs').write_text("module.exports = value => { if (!Number.isFinite(value)) throw new TypeError('finite number required'); return Math.max(0,Math.min(10,value)); };\n")
        green=run(['node','--test','--test-reporter=tap','value.test.cjs'],small)
        assert green['exit']==0 and '# pass 5' in green['stdout'],green
        report={'baseline_revision':args.baseline_revision,'source_revision':args.source_revision,'samples':results,
                'card1':{'test_sha256':hashlib.sha256(tests.encode()).hexdigest(),'red':red,'green':green},
                'limits':['generation time is native CLI time, not model latency','normalization operations are actual fixture file operations, not observed human effort',
                          'UI/API fixture is identical in both versions; no model productivity or general business gain claimed']}
        with args.output.open('x', encoding='utf-8') as output:
            json.dump(report, output, ensure_ascii=False, indent=2)
            output.write('\n')
        print('PASS four matched generation samples; CARD-1 native red -> green (5 cases)')
        for row in results:print(row['card'],row['version'],row['initial_count'],row['first_pass_material_shape'],row['normalization_count'])
    return 0
if __name__=='__main__':raise SystemExit(main())
