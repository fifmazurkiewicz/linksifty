begin;
select plan(19);
select is(public.default_assessment_rubric()->>'version','2','new settings use calibrated rules');
select ok(public.valid_assessment_rubric(public.legacy_assessment_rubric()),'unversioned historical rules remain valid');
select ok(not public.valid_assessment_rubric(jsonb_set(public.default_assessment_rubric(),'{version}','3')),'unknown version rejected');
select ok(not public.valid_assessment_rubric(jsonb_set(public.default_assessment_rubric(),'{version}','true')),'boolean version rejected');
insert into auth.users(id,email) values ('cccccccc-cccc-4ccc-8ccc-cccccccccccc','calibration@example.test');
select public.get_or_create_account_profile('cccccccc-cccc-4ccc-8ccc-cccccccccccc','calibration@example.test',true);
select public.submit_search_items('cccccccc-cccc-4ccc-8ccc-cccccccccccc',array['https://calibration.example/article']);
create temporary table calibration_job as select * from public.claim_processing_job('cccccccc-cccc-4ccc-8ccc-cccccccccccc');
select public.save_job_source(user_id,id,lease_token,repeat('Exact primary material. ',30)) from calibration_job;
create temporary table calibration_sources as select jsonb_build_object('status','ready','sources',jsonb_agg(jsonb_build_object('id','external-'||n,'url','https://source'||n||'.example','text','Exact external material.'))) as context from generate_series(1,20) n;
select throws_ok(format('select public.save_research_context(%L,%L,%L,%L)',j.user_id,j.id,j.lease_token,
 jsonb_set(s.context,'{sources}',(s.context->'sources')||jsonb_build_array(jsonb_build_object('id','extra','url','https://extra.example','text','Another external material.')))),
 'P0001','invalid_research_context','21 additional sources rejected') from calibration_job j cross join calibration_sources s;
select is((select count(*)::int from calibration_job j cross join calibration_sources s cross join lateral public.save_research_context(j.user_id,j.id,j.lease_token,s.context)),1,'20 additional sources saved');
create temporary table calibration_res as select r.* from calibration_job j cross join lateral public.reserve_analysis(j.user_id,j.id,j.lease_token,0.1) r;
select is((select rubric_snapshot->>'version' from calibration_res),'2','reservation snapshots v2');
select public.settle_analysis(user_id,id,0.01) from calibration_res;
create temporary table calibration_payload as select jsonb_build_object('note','No verification available','score',null,'verdict','to_review','hype_signals','[]'::jsonb,'verdict_reason','Key claims unverified','criteria',jsonb_agg(jsonb_build_object('name',r->>'name','score',null,'status',case when r->>'name'='replicability' then 'not_applicable' else 'not_verified' end,'rationale','Inspected but not established','citation_ids',jsonb_build_array('dddddddd-dddd-4ddd-8ddd-dddddddddddd')))) as body,
 '[{"id":"dddddddd-dddd-4ddd-8ddd-dddddddddddd","source_id":"primary","excerpt":"Exact primary material.","start_position":0,"end_position":23}]'::jsonb as citations
 from jsonb_array_elements(public.default_assessment_rubric()->'criteria') r;
select throws_ok(format('select public.complete_processing_job(%L,%L,%L,%L,%L)',j.user_id,j.id,j.lease_token,jsonb_set(p.body,'{verdict}','"hype"'),p.citations),'P0001','invalid_hype_evidence','hype cannot be inferred from an unscored assessment') from calibration_job j cross join calibration_payload p;
select throws_ok(format('select public.complete_processing_job(%L,%L,%L,%L,%L)',j.user_id,j.id,j.lease_token,jsonb_set(p.body,'{criteria,0,score}','1'),p.citations),'P0001','invalid_assessment','unknown cannot carry a numeric penalty') from calibration_job j cross join calibration_payload p;
select throws_ok(format('select public.complete_processing_job(%L,%L,%L,%L,%L)',j.user_id,j.id,j.lease_token,jsonb_set(p.body,'{criteria,0,status}','"not_applicable"'),p.citations),'P0001','invalid_assessment','N/A restricted to replicability') from calibration_job j cross join calibration_payload p;
select throws_ok(format('select public.complete_processing_job(%L,%L,%L,%L,%L)',j.user_id,j.id,j.lease_token,
 jsonb_set(jsonb_set(p.body,'{verdict}','"hype"'),'{hype_signals}','[{"rationale":"Overclaim","citation_ids":["eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee"]}]'),p.citations),'P0001','invalid_hype_evidence','hype needs an existing primary citation') from calibration_job j cross join calibration_payload p;
select is((select count(*)::int from calibration_job j cross join calibration_payload p cross join lateral public.complete_processing_job('ffffffff-ffff-4fff-8fff-ffffffffffff',j.id,j.lease_token,p.body,p.citations)),0,'foreign owner cannot save calibrated assessment');
select is((select count(*)::int from calibration_job j cross join calibration_payload p cross join lateral public.complete_processing_job(j.user_id,j.id,j.lease_token,p.body,p.citations)),1,'unscored assessment persists');
select ok((select score is null from public.assessments where user_id='cccccccc-cccc-4ccc-8ccc-cccccccccccc'),'no false zero percentage stored');
select is((select verdict::text from public.assessments where user_id='cccccccc-cccc-4ccc-8ccc-cccccccccccc'),'to_review','unverified material goes to review');
select is((select criteria->4->>'status' from public.assessments where user_id='cccccccc-cccc-4ccc-8ccc-cccccccccccc'),'not_applicable','N/A survives persistence');
select ok(not has_function_privilege('authenticated','public.complete_processing_job(uuid,uuid,uuid,jsonb,jsonb)','execute'),'client cannot write assessments');
-- A fresh owner job verifies the successful hype path and rejects secondary evidence.
select public.submit_fetch_items('cccccccc-cccc-4ccc-8ccc-cccccccccccc',array['https://calibration.example/hype']);
create temporary table hype_job as select * from public.claim_processing_job('cccccccc-cccc-4ccc-8ccc-cccccccccccc');
select public.save_job_source(user_id,id,lease_token,repeat('Exact primary material. ',30)) from hype_job;
select public.save_research_context(j.user_id,j.id,j.lease_token,s.context) from hype_job j cross join calibration_sources s;
create temporary table hype_res as select r.* from hype_job j cross join lateral public.reserve_analysis(j.user_id,j.id,j.lease_token,0.1) r;
select public.settle_analysis(user_id,id,0.01) from hype_res;
select throws_ok(format('select public.complete_processing_job(%L,%L,%L,%L,%L)',j.user_id,j.id,j.lease_token,
 jsonb_set(jsonb_set(p.body,'{verdict}','"hype"'),'{hype_signals}','[{"rationale":"Overclaim","citation_ids":["eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee"]}]'),
 p.citations||'[{"id":"eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee","source_id":"external-1","excerpt":"Exact external material.","start_position":0,"end_position":24}]'::jsonb),
 'P0001','invalid_hype_evidence','a real comparison-source citation cannot establish primary-source hype') from hype_job j cross join calibration_payload p;
select public.complete_processing_job(j.user_id,j.id,j.lease_token,
 jsonb_set(jsonb_set(p.body,'{verdict}','"hype"'),'{hype_signals}','[{"rationale":"Overclaim in primary material","citation_ids":["ffffffff-ffff-4fff-8fff-ffffffffffff"]}]')
 ||jsonb_build_object('criteria',(select jsonb_agg(jsonb_set(c,'{citation_ids}','["ffffffff-ffff-4fff-8fff-ffffffffffff"]')) from jsonb_array_elements(p.body->'criteria') c)),
 jsonb_set(p.citations,'{0,id}','"ffffffff-ffff-4fff-8fff-ffffffffffff"')) from hype_job j cross join calibration_payload p;
select is((select a.hype_signals->0->>'rationale' from public.assessments a join hype_job j on j.item_id=a.item_id),'Overclaim in primary material','grounded hype survives persistence');
select * from finish();
rollback;
