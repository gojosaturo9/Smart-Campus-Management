insert into public.branches (department_id, name, code)
select id, 'Computer Science Engineering', 'CSE'
from public.departments
where code in ('CS', 'CSE')
on conflict do nothing;

insert into public.branches (department_id, name, code)
select id, 'Artificial Intelligence and Machine Learning', 'AI-ML'
from public.departments
where code in ('CS', 'CSE')
on conflict do nothing;

insert into public.branches (department_id, name, code)
select id, 'Artificial Intelligence and Data Science', 'AI-DS'
from public.departments
where code in ('CS', 'CSE')
on conflict do nothing;

insert into public.branches (department_id, name, code)
select id, 'Cyber Security', 'CYBER'
from public.departments
where code in ('CS', 'CSE')
on conflict do nothing;

insert into public.branches (department_id, name, code)
select id, 'Data Science', 'DS'
from public.departments
where code in ('CS', 'CSE')
on conflict do nothing;
