-- Calibrated rubric v2. Historical snapshots and scores are deliberately untouched.
create function public.legacy_assessment_rubric() returns jsonb
language sql immutable set search_path=public as $rubric$
select '{"criteria": [{"name": "novelty", "description": "Does the material offer new information or a useful new perspective?", "weight": 1}, {"name": "evidence", "description": "Are its claims supported by concrete data, examples and cited evidence?", "weight": 2}, {"name": "practicality", "description": "Can the reader apply the information to a real task or decision?", "weight": 1}, {"name": "source_credibility", "description": "Is the author or publisher qualified, transparent and trustworthy?", "weight": 2}, {"name": "replicability", "description": "Are there enough methods and details to reproduce the actions or results?", "weight": 2}, {"name": "independent_corroboration", "description": "Do independent supplied sources corroborate the claims?", "weight": 1}, {"name": "absence_of_conflict_of_interest", "description": "Are interests disclosed and promotional incentives unlikely to distort the claims?", "weight": 2}, {"name": "concreteness", "description": "Does the material provide specific details rather than slogans or superlatives?", "weight": 1}]}'::jsonb;
$rubric$;

create or replace function public.valid_assessment_rubric(p_rubric jsonb) returns boolean
language plpgsql immutable set search_path=public as $$
declare e jsonb; seen text[] := '{}'; allowed text[] := array[
 'novelty','evidence','practicality','source_credibility','replicability',
 'independent_corroboration','absence_of_conflict_of_interest','concreteness'];
begin
 if p_rubric is null or jsonb_typeof(p_rubric) <> 'object' then return false; end if;
 if p_rubric - array['criteria','version'] <> '{}'::jsonb or jsonb_typeof(p_rubric->'criteria') is distinct from 'array' then return false; end if;
 if p_rubric ? 'version' and (jsonb_typeof(p_rubric->'version') is distinct from 'number' or p_rubric->>'version' not in ('1','2')) then return false; end if;
 if jsonb_array_length(p_rubric->'criteria') <> 8 then return false; end if;
 for e in select * from jsonb_array_elements(p_rubric->'criteria') loop
  if jsonb_typeof(e) <> 'object' then return false; end if;
  if e - array['name','description','weight'] <> '{}'::jsonb
   or jsonb_typeof(e->'name') is distinct from 'string'
   or jsonb_typeof(e->'description') is distinct from 'string'
   or jsonb_typeof(e->'weight') is distinct from 'number' then return false; end if;
  if not (e->>'name' = any(allowed)) or e->>'name' = any(seen)
   or e->>'weight' !~ '^(10|[1-9])$'
   or length(e->>'description') not between 1 and 1000
   or length(btrim(e->>'description', chr(9) || chr(10) || chr(11) || chr(12) || chr(13) || chr(28) || chr(29) || chr(30) || chr(31) || chr(32) || chr(133) || chr(160) || chr(5760) || chr(8192) || chr(8193) || chr(8194) || chr(8195) || chr(8196) || chr(8197) || chr(8198) || chr(8199) || chr(8200) || chr(8201) || chr(8202) || chr(8232) || chr(8233) || chr(8239) || chr(8287) || chr(12288)))=0 then return false; end if;
  seen := array_append(seen,e->>'name');
 end loop;
 return true;
end;
$$;


create or replace function public.default_assessment_rubric() returns jsonb
language sql immutable set search_path=public as $rubric$
select '{"version":2,"criteria":[{"name":"novelty","description":"Learning value: does the material build useful understanding within its purpose? 1: little substantive explanation; 3: some useful knowledge with gaps; 5: clear, substantial learning even about established facts. Do not assume the reader''s prior knowledge or require global novelty; state that personalization is unavailable.","weight":1},{"name":"evidence","description":"Support for claims: do the key claims have relevant, traceable legislation, data, documents or examples? 1: identifiable unsupported or contradicted key claims; 3: partial support with named gaps; 5: strong support for the central claims. Check dates and scope for time-sensitive claims. Numbers alone are not evidence. Use not_verified when the supplied material cannot establish support.","weight":2},{"name":"practicality","description":"Usefulness: can the reader use this to understand a topic, make a decision or act? 1: little usable information; 3: useful but missing important decision details; 5: clearly supports its intended task or decision. An explainer need not provide a click-by-click tutorial or investment strategy.","weight":1},{"name":"source_credibility","description":"Topic-specific credibility: is the identified author or institution competent and accountable in this topic? 1: concrete credibility problems; 3: relevant but limited authority; 5: a competent, accountable primary authority in its remit. Official guidance can merit 5; a government URL is not an automatic guarantee of correctness or currency. Use not_verified when identity or competence cannot be established.","weight":2},{"name":"replicability","description":"Replicability: only for a claimed experiment, method or reproducible result. 1: crucial steps missing; 3: enough for partial reproduction with named gaps; 5: sufficient methods, inputs and conditions to reproduce it. Use not_applicable for informational explainers that do not claim such a method or result.","weight":2},{"name":"independent_corroboration","description":"Cross-source confirmation: compare specific central claims with supplied independent sources. 1: concrete contradiction; 3: limited or mixed confirmation; 5: central claims clearly corroborated. Identify the matching claim and sources. Different levels of detail are not a contradiction. Use not_verified if no independent comparison can be established; the presence of another page alone is insufficient.","weight":1},{"name":"absence_of_conflict_of_interest","description":"Fair presentation and interests: does the source disclose relevant interests and present claims without sales-driven distortion? 1: concrete hidden interests or material distortion; 3: identifiable incentives with limitations; 5: fair presentation with adequately understood interests and no material distortion observed. Missing a disclosure is not proof of conflict. Use not_verified when context is insufficient.","weight":2},{"name":"concreteness","description":"Specificity and completeness for the stated purpose: does the material give relevant details, conditions and limitations? 1: slogans or critical omissions; 3: useful specifics but named gaps; 5: concrete details sufficient for its purpose. Consider currency where it matters; do not demand an entire investing guide from an explanation of account rules.","weight":1}]}'::jsonb;
$rubric$;

-- Only default descriptions are replaced; custom wording and every weight survive.
update public.settings s set rubric=jsonb_build_object('version',2,'criteria',(
 select jsonb_agg(jsonb_set(e,'{description}',case
   when e->>'description'=o->>'description' then n->'description' else e->'description' end) order by ord)
 from jsonb_array_elements(s.rubric->'criteria') with ordinality as entries(e,ord)
 join jsonb_array_elements(public.legacy_assessment_rubric()->'criteria') o on o->>'name'=e->>'name'
 join jsonb_array_elements(public.default_assessment_rubric()->'criteria') n on n->>'name'=e->>'name'
)) where coalesce((rubric->>'version')::int,1)=1;

alter table public.assessments alter column score drop not null;
alter table public.assessments alter column rubric_snapshot set default public.legacy_assessment_rubric();
alter table public.assessments add column hype_signals jsonb not null default '[]'::jsonb
 check(jsonb_typeof(hype_signals)='array' and jsonb_array_length(hype_signals)<=3);
alter table public.assessments add column verdict_reason text not null default '';

create or replace function public.save_research_context(p_user_id uuid,p_job_id uuid,p_lease uuid,p_context jsonb)
returns setof public.jobs language plpgsql security definer set search_path=public as $$
begin
  if p_context is null or jsonb_typeof(p_context->'sources') is distinct from 'array' or jsonb_array_length(p_context->'sources')>20 or octet_length(p_context::text)>1200000 then raise exception 'invalid_research_context'; end if;
  if p_context->>'status' not in ('not_requested','unavailable','uncertain','budget_exhausted','no_sources','ready')
    or exists(select 1 from jsonb_array_elements(p_context->'sources') s where s->>'id' is null or s->>'id'='primary'
      or s->>'url' !~ '^https?://' or length(s->>'text') not between 1 and 12000)
    or (select count(*) from jsonb_array_elements(p_context->'sources')) <> (select count(distinct s->>'id') from jsonb_array_elements(p_context->'sources') s)
    then raise exception 'invalid_research_context'; end if;
  return query update public.jobs set search_context=p_context,updated_at=now()
   where id=p_job_id and user_id=p_user_id and lease_token=p_lease and lease_expires_at>now() and status='processing' and search_context is null returning *;
end;
$$;

create or replace function public.complete_processing_job(p_user_id uuid, p_job_id uuid, p_lease uuid, p_assessment jsonb, p_citations jsonb)
returns setof public.items language plpgsql security definer set search_path = public as $$
declare j public.jobs; a uuid; c jsonb; source_text text; source_link text; entry jsonb; signal jsonb;
begin
  select * into j from public.jobs where id = p_job_id and user_id = p_user_id and lease_token = p_lease and lease_expires_at > now() for update;
  if not found then return; end if;
  if not exists (select 1 from public.source_contents where item_id = j.item_id and user_id = p_user_id)
    or not exists (select 1 from public.usage_reservations where id = j.reservation_id and user_id = p_user_id and state = 'settled') then return; end if;
  if coalesce((j.rubric_snapshot->>'version')::int,1)=2 then
    if jsonb_typeof(p_assessment->'criteria') is distinct from 'array'
      or jsonb_array_length(p_assessment->'criteria')<>8
      or (select count(distinct x->>'name') from jsonb_array_elements(p_assessment->'criteria') x)<>8
      or jsonb_typeof(p_assessment->'hype_signals') is distinct from 'array'
      or jsonb_array_length(p_assessment->'hype_signals')>3
      then raise exception 'invalid_assessment'; end if;
    for entry in select * from jsonb_array_elements(p_assessment->'criteria') loop
      if not exists(select 1 from jsonb_array_elements(j.rubric_snapshot->'criteria') r where r->>'name'=entry->>'name')
        or entry->>'status' is null or entry->>'status' not in ('assessed','not_applicable','not_verified')
        or (entry->>'status'='assessed' and (jsonb_typeof(entry->'score') is distinct from 'number' or entry->>'score' !~ '^[1-5]$'))
        or (entry->>'status'<>'assessed' and jsonb_typeof(entry->'score') is distinct from 'null')
        or (entry->>'status'='not_applicable' and entry->>'name'<>'replicability')
        or jsonb_typeof(entry->'citation_ids') is distinct from 'array'
        or jsonb_array_length(entry->'citation_ids')=0
        or exists(select 1 from jsonb_array_elements_text(entry->'citation_ids') cid where not exists(
          select 1 from jsonb_array_elements(p_citations) cited where cited->>'id'=cid))
        then raise exception 'invalid_assessment'; end if;
    end loop;
    for signal in select * from jsonb_array_elements(p_assessment->'hype_signals') loop
      if coalesce(btrim(signal->>'rationale'),'')='' or jsonb_typeof(signal->'citation_ids') is distinct from 'array'
        or jsonb_array_length(signal->'citation_ids')=0
        or exists(select 1 from jsonb_array_elements_text(signal->'citation_ids') cid where not exists(
          select 1 from jsonb_array_elements(p_citations) cited where cited->>'id'=cid and coalesce(cited->>'source_id','primary')='primary'))
        then raise exception 'invalid_hype_evidence'; end if;
    end loop;
    if (p_assessment->>'verdict'='hype') <> (jsonb_array_length(p_assessment->'hype_signals')>0)
      then raise exception 'invalid_hype_evidence'; end if;
  end if;
  insert into public.assessments(item_id, user_id, note, criteria, score, verdict, threshold_snapshot, rubric_snapshot, hype_signals, verdict_reason)
    values (j.item_id, p_user_id, p_assessment->>'note', p_assessment->'criteria', (p_assessment->>'score')::numeric,
    (p_assessment->>'verdict')::public.verdict, j.threshold_snapshot,coalesce(j.rubric_snapshot,public.legacy_assessment_rubric()),coalesce(p_assessment->'hype_signals','[]'::jsonb),coalesce(p_assessment->>'verdict_reason','')) returning id into a;
  for c in select * from jsonb_array_elements(p_citations) loop
    if coalesce(c->>'source_id', 'primary') = 'primary' then
      select sc.content, i.original_url into source_text, source_link from public.source_contents sc
        join public.items i on i.id=sc.item_id where sc.item_id=j.item_id and sc.user_id=p_user_id;
    else
      select s->>'text', s->>'url' into source_text, source_link
        from jsonb_array_elements(j.search_context->'sources') s where s->>'id'=c->>'source_id';
    end if;
    if source_text is null or (c->>'start_position')::int < 0 or (c->>'end_position')::int <= (c->>'start_position')::int
      or substring(source_text from (c->>'start_position')::int+1 for (c->>'end_position')::int-(c->>'start_position')::int) <> c->>'excerpt'
      then raise exception 'invalid_citation'; end if;
    insert into public.citations(id, assessment_id, user_id, excerpt, start_position, end_position, source_url, source_id)
      values ((c->>'id')::uuid, a, p_user_id, c->>'excerpt', (c->>'start_position')::int, (c->>'end_position')::int, source_link, coalesce(c->>'source_id','primary'));
  end loop;
  update public.jobs set status = 'completed', processing_stage = 'completed', model_result = null, lease_token = null, lease_expires_at = null, updated_at = now() where id = j.id;
  return query update public.items set status = 'completed', processing_stage = 'completed', failure_reason = null, updated_at = now()
    where items.id = j.item_id and items.user_id = p_user_id returning *;
end;
$$;


revoke execute on function public.legacy_assessment_rubric() from public,anon,authenticated;
grant execute on function public.legacy_assessment_rubric() to service_role;
notify pgrst, 'reload schema';
