import copy
import unittest
import json
import tempfile
from pathlib import Path
from tracker.adapters import normalize
from tracker.eligibility import classify
from tracker.engine import reconcile, public_view


def job(**changes):
    value = dict(id='1', requisition_id=None, title='Software Engineer, New Grad', location='San Francisco, CA', countries=[], description='Full-time. Graduating in 2027.', employment_type='FullTime', url='https://example.com/jobs/1', source='ashby', employer_posted_at=None, employer_published_at=None, employer_updated_at=None)
    value.update(changes)
    return value


class TrackerTests(unittest.TestCase):
    def test_release_order_keeps_closed_at_bottom(self):
        from tracker.presentation import listing_order, button
        base = dict(employer='Employer', title='Role', location='US', url='https://example.com/posting', first_seen_at='2026-10-05')
        jobs = [dict(base, id='closed-old', status='closed', employer_published_at='2026-08-01'),
                dict(base, id='open-unknown', status='open', employer_published_at=None),
                dict(base, id='closed-new', status='closed', employer_published_at='2026-10-05'),
                dict(base, id='open-old', status='open', employer_published_at='2026-09-01'),
                dict(base, id='open-new', status='open', employer_published_at='2026-10-01')]
        self.assertEqual([j['id'] for j in listing_order(jobs)], ['open-new', 'open-old', 'open-unknown', 'closed-new', 'closed-old'])
        self.assertIn('https://example.com/posting', button(jobs[0]))
        self.assertIn('closed.svg', button(jobs[0]))

    def test_unavailable_stub_does_not_overwrite_or_close(self):
        state = {}; employer = {'id':'e', 'name':'Employer'}
        reconcile(state, employer, [job()], '2026-10-05T10:00:00+00:00')
        reconcile(state, employer, [dict(id='1', _unavailable=True)], '2026-10-05T11:00:00+00:00')
        self.assertEqual(state['jobs']['e:1']['title'], job()['title'])
        self.assertEqual(state['jobs']['e:1']['status'], 'open')

    def test_jsonld_and_workday_dates(self):
        from tracker.adapters import jsonld_job, workday_job
        page = '<script type="application/ld+json">' + json.dumps({'@type':'JobPosting', 'title':'Software Engineer', 'description':'Full-time entry level', 'employmentType':'FULL_TIME', 'datePosted':'2026-09-20', 'jobLocation':{'address':{'addressCountry':{'name':'US'}, 'addressLocality':'Seattle', 'addressRegion':'WA'}}}) + '</script>'
        normalized = jsonld_job({'id':'1', 'url':'https://example.com/1'}, page)
        self.assertEqual(normalized['employer_published_at'], '2026-09-20')
        self.assertEqual(normalized['employment_type'], 'FULLTIME')
        self.assertEqual(normalized['countries'], ['US'])
        info = dict(id='1', jobReqId='r', title='2027 New Grad Software Engineer', location='Seattle, WA', jobDescription='Full-time', externalUrl='https://example.com/1', startDate='2026-09-20', country={'descriptor':'United States of America'}, timeType='Full time')
        self.assertEqual(workday_job({'jobPostingInfo':info})['employer_published_at'], '2026-09-20')
        self.assertIsNone(workday_job({'jobPostingInfo':dict(info, posted=False)}))

    def test_manual_expiry_and_reverification(self):
        from tracker.manual import seed
        employer = {'id':'e', 'name':'Employer'}
        manual = job(employer_id='e', employer='Employer', manual_verified_at='2026-10-05T10:00:00+00:00')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'manual.json'
            path.write_text(json.dumps({'jobs':[manual]}))
            state = {'jobs':{}, 'health':{}}
            seed(state, path)
            view = public_view(state, [employer], '2026-10-07T11:00:00+00:00', classify)
            self.assertTrue(view['jobs'][0]['status'].startswith('verification overdue'))
            self.assertEqual(view['coverage'][0]['coverage'], 'planned')
            manual['manual_verified_at'] = '2026-10-07T12:00:00+00:00'
            path.write_text(json.dumps({'jobs':[manual]}))
            seed(state, path)
            refreshed = public_view(state, [employer], '2026-10-07T12:01:00+00:00', classify)['jobs'][0]
            self.assertTrue(refreshed['status'].startswith('open'))
            self.assertEqual(refreshed['first_seen_at'], '2026-10-05T10:00:00+00:00')

    def test_publication_cutoff(self):
        for title in ['Software Engineer, New Grad 2027', 'Software Engineer I']:
            self.assertIsNone(classify(job(title=title, employer_published_at='2025-12-31T23:59:59Z', employer_updated_at='2026-10-05')))
            self.assertIsNotNone(classify(job(title=title, employer_published_at='2026-01-01')))
        self.assertIsNone(classify(job(_recovered=True, employer_posted_at='2024-07-01')))
        self.assertIsNotNone(classify(job(employer_published_at=None)))
        reused = job(employer_original_posted_at='2020-10-27', current_cycle=2027, cycle_source='https://example.com/early-talent', description='Full-time new graduate')
        self.assertTrue(classify(reused)['eligibility'].startswith('2027'))
        self.assertIsNone(classify(dict(reused, employer_published_at='2020-10-27')))

    def test_eligibility(self):
        self.assertIsNotNone(classify(job()))
        for changes in [dict(location='Remote'), dict(countries=['Canada']), dict(title='Senior Software Engineer, New Grad'), dict(employment_type='Intern'), dict(description='Full-time graduating in 2026'), dict(description='New grad. 3+ years of experience required'), dict(title='Software Engineer, New Grad (Dec 2026)', description='Graduate in December 2026 and start full time by January 2027')]:
            self.assertIsNone(classify(job(**changes)), changes)
        self.assertIsNotNone(classify(job(description='Full-time entry level')))

    def test_failures_and_omissions(self):
        state = {}; employer = {'id':'e', 'name':'Employer'}
        reconcile(state, employer, [job()], '2026-10-05T10:00:00+00:00')
        reconcile(state, employer, [], '2026-10-05T10:05:00+00:00', 'timeout')
        self.assertEqual(state['jobs']['e:1']['status'], 'open')
        for minute in [10,15,20]:
            reconcile(state, employer, [], f'2026-10-05T10:{minute}:00+00:00')
        self.assertNotEqual(state['jobs']['e:1']['status'], 'closed')
        reconcile(state, employer, [], '2026-10-05T10:40:00+00:00')
        self.assertEqual(state['jobs']['e:1']['status'], 'closed')
        reconcile(state, employer, [job()], '2026-10-05T10:45:00+00:00')
        self.assertEqual(state['jobs']['e:1']['first_seen_at'], '2026-10-05T10:00:00+00:00')
        self.assertNotIn('first_missing_at',state['jobs']['e:1'])

    def test_poll_does_not_change_publication(self):
        state={}; employer={'id':'e','name':'Employer','source':{'adapter':'ashby','board':'e'}}
        reconcile(state,employer,[job()],'2026-10-05T10:00:00+00:00')
        before=public_view(state,[employer],'2026-10-05T10:00:00+00:00',classify)
        reconcile(state,employer,[job()],'2026-10-05T10:05:00+00:00')
        self.assertEqual(before,public_view(state,[employer],'2026-10-05T10:05:00+00:00',classify))

    def test_recovery_preserves_eligibility(self):
        recovered=job(_recovered=True, description='', eligibility='2027 mentioned — review requirements', employment='full-time', evidence='2027 graduates', review_required=True)
        self.assertEqual(classify(recovered)['evidence'], '2027 graduates')

    def test_requisition_dedup(self):
        state={}; employer={'id':'e','name':'Employer'}
        reconcile(state,employer,[job(id='a',requisition_id='r'),job(id='b',requisition_id='r')],'2026-10-05T10:00:00+00:00')
        self.assertEqual(len(state['jobs']),1)
        self.assertEqual(len(state['jobs']['e:r']['source_links']),1)

    def test_adapter_contracts(self):
        greenhouse={'jobs':[{'id':1,'title':'Software Engineer','absolute_url':'https://example.com/1','location':{'name':'New York'},'content':'<p>Full-time</p>','updated_at':'2026-01-01'}]}
        g=normalize({'adapter':'greenhouse'},greenhouse)[0]
        self.assertIsNone(g['employer_posted_at'])
        self.assertEqual(g['description'],'Full-time')
        lever=[{'id':'1','text':'Software Engineer','hostedUrl':'https://example.com/1','categories':{'location':'Boston','commitment':'Full-time'},'lists':[{'content':'<p>2027 graduates</p>'}]}]
        self.assertIn('2027',normalize({'adapter':'lever'},lever)[0]['description'])
        ashby={'jobs':[dict(id='1',title='Software Engineer',location='Boston',jobUrl='https://example.com/1',isListed=False)]}
        self.assertEqual(normalize({'adapter':'ashby'},ashby),[])
        with self.assertRaises((KeyError,ValueError)):
            normalize({'adapter':'ashby'},{'broken':[]})


if __name__ == '__main__':
    unittest.main()
