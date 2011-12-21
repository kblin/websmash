# -*- coding: utf-8 -*-
from minimock import Mock, TraceTracker, assert_same_trace
import websmash
import os
from werkzeug import FileStorage
from websmash.models import Job
from websmash.views import sec_met_types
from tests.test_shared import WebsmashTestCase

class WebTestCase(WebsmashTestCase):
    def test_startpage(self):
        """Test if startpage has a "Submit Query" button"""
        rv = self.client.get('/')
        assert "Submit Query" in rv.data

    def test_downloadpage(self):
        """Test if download page works"""
        rv = self.client.get('/download')
        assert "The current version of antiSMASH is 1.2" in rv.data

    def test_helppage(self):
        """Test if help page works"""
        rv = self.client.get('/help')
        assert "antiSMASH Help" in rv.data

    def test_aboutpage(self):
        """Test if about page works"""
        rv = self.client.get('/about')
        assert "About antiSMASH" in rv.data

    def test_contactpage(self):
        """Test if contact form is displayed"""
        rv = self.client.get('/contact')
        assert "you can contact us with this form" in rv.data

    def test_contactpage_no_email(self):
        """Test if contact form complains without an email address"""
        test_body = "Test body"
        rv = self.client.post('/contact', data=dict(body=test_body),
                           follow_redirects=True)
        assert "Please specify an email address" in rv.data
        assert test_body in rv.data

    def test_contactpage_no_message(self):
        """Test if contact form complains without a message"""
        email = "ex@mp.le"
        rv = self.client.post('/contact', data=dict(email=email),
                           follow_redirects=True)
        assert "No message specified. Please specify a message" in rv.data
        assert email in rv.data

    def test_contactpage_sent_mail(self):
        """Test if contact page reports that it sent a message"""
        data = dict(email="ex@mp.le", body="Test body")
        with websmash.mail.record_messages() as outbox:
            rv = self.client.post('/contact', data=data, follow_redirects=True)
            assert "Your message was successfully sent." in rv.data
            assert data['body'] in rv.data
            assert len(outbox) == 2
            contact_msg = outbox[0]
            confirm_msg = outbox[1]
            assert contact_msg.subject == 'antiSMASH feedback'
            assert data['body'] in contact_msg.body
            assert confirm_msg.subject == 'antiSMASH feedback received'
            assert data['body'] in confirm_msg.body

    def test_submit_job_upload(self):
        """Test if submitting a job with an uploaded sequence works"""
        data = dict(seq=self.tmp_file, cluster_1=u'on')
        rv = self.client.post('/', data=data, follow_redirects=True)
        assert "Status of job" in rv.data

    def test_geneclustertypes_all(self):
        """Test if the 'all' checkbox results in geneclustertypes being 1"""
        data = dict(seq=self.tmp_file, cluster_1=u'on', cluster_5=u'on')
        rv = self.client.post('/', data=data, follow_redirects=True)
        assert "Status of job" in rv.data
        j = Job.query.filter(Job.status=='pending').first()
        assert j is not None
        assert j.geneclustertypes == '1'

    def test_geneclustertypes_specific(self):
        """Test if geneclustertypes matches checked boxes"""
        data = dict(seq=self.tmp_file, cluster_2=u'on', cluster_5=u'on')
        rv = self.client.post('/', data=data, follow_redirects=True)
        assert "Status of job" in rv.data
        j = Job.query.filter(Job.status=='pending').first()
        assert j is not None
        self.assertEquals(j.geneclustertypes, '2,5')

    def test_geneclustertypes_last(self):
        """Test if geneclustertypes is correct for last checkbox"""
        last = len(sec_met_types)
        data = dict(seq=self.tmp_file)
        data['cluster_%d' % last] = u'on'
        rv = self.client.post('/', data=data, follow_redirects=True)
        assert "Status of job" in rv.data
        j = Job.query.filter(Job.status=='pending').first()
        assert j is not None
        self.assertEquals(j.geneclustertypes, u'%d' % last)

    def test_geneclustertypes_none(self):
        """Check if specifying no gene clusters will give an error"""
        rv = self.client.post('/', data={}, follow_redirects=True)
        expected = "No gene cluster types specified. Please select the type "
        expected += "of secondary metabolites to look for."
        assert expected in rv.data

    def test_taxon_default(self):
        """Test if taxon default is "prokaryote" for DNA uploads"""
        data = dict(seq=self.tmp_file, cluster_1=u'on')
        rv = self.client.post('/', data=data, follow_redirects=True)
        assert "Status of job" in rv.data
        j = Job.query.filter(Job.status=='pending').first()
        assert j is not None
        self.assertEquals(j.taxon, 'p')

    def test_submit_job_download_url_raises(self):
        """Test if a job with accession# errors out when download fails"""
        data = dict(ncbi='TESTING', cluster_1=u'on')
        tt = TraceTracker()
        self.dl.download = Mock('dl.download', tracker=tt)
        rv = self.client.post('/', data=data)
        assert "Downloading or uploading input file failed!" in rv.data

    def test_submit_job_download_url_correct(self):
        """Test if a job with accession# uses right download URL"""
        data = dict(ncbi='TESTING', cluster_1=u'on')
        tt = TraceTracker()
        self.dl.download = Mock('dl.download', tracker=tt)
        rv = self.client.post('/', data=data)

        expected =  'Called dl.download(\n    \''
        expected += 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi'
        expected += '?db=protein&email="%s"&tool="antiSMASH"&' % \
                    self.app.config['DEFAULT_MAIL_SENDER']
        expected += 'val="TESTING"&dopt=gbwithparts\')\n'

        assert_same_trace(tt, expected)

    def test_submit_job_download_url_correct_email(self):
        """Test if a job with accession# adds user email to download URL"""
        data = dict(ncbi='TESTING', email="ex@mp.le", cluster_1=u'on')
        tt = TraceTracker()
        self.dl.download = Mock('dl.download', tracker=tt)
        rv = self.client.post('/', data=data)

        expected =  'Called dl.download(\n    \''
        expected += 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi'
        expected += '?db=protein&email="ex@mp.le"&tool="antiSMASH"&'
        expected += 'val="TESTING"&dopt=gbwithparts\')\n'

        assert_same_trace(tt, expected)


    def test_submit_job_download(self):
        """Test if submitting a job with a downloaded sequence works"""
        data = dict(ncbi='TESTING', cluster_1=u'on')
        tmp_file = open(os.path.join(self.tmpdir, 'test.fa'), 'w')
        tmp_file.write('>test\nATGACCGAGAGTACATAG\n')
        tmp_file.close()
        tmp_file = open(os.path.join(self.tmpdir, 'test.fa'))
        tt = TraceTracker()
        self.dl.download = Mock('dl.download', tracker=tt)
        self.dl.download.mock_returns = FileStorage(stream=tmp_file)
        rv = self.client.post('/', data=data, follow_redirects=True)
        assert "Status of job" in rv.data

    def test_submit_job_fullhmm(self):
        """Test if switching on the full genome hmmer works"""
        data = dict(seq=self.tmp_file, cluster_1=u'on', fullhmmer=u'on')
        rv = self.client.post('/', data=data, follow_redirects=True)
        assert "Status of job" in rv.data
        j = Job.query.filter(Job.status=='pending').first()
        assert j is not None
        assert j.fullhmm

    def test_submit_job_from_to(self):
        """Test if submitting a job with an uploaded sequence works"""
        data = dict(seq=self.tmp_file, cluster_1=u'on')
        # Can't pass a python keyword in dict()
        data['from'] = '23'
        data['to'] = '42'
        rv = self.client.post('/', data=data, follow_redirects=True)
        assert "Status of job" in rv.data
        j = Job.query.filter(Job.status=='pending').first()
        self.assertEqual(j.from_pos, 23)
        self.assertEqual(j.to_pos, 42)

    def test_display(self):
        """Test if displaying jobs works as expected"""
        rv = self.client.get('/display/invalid')
        self.assert404(rv)
        j = Job()
        self.db.session.add(j)
        self.db.session.commit()
        rv = self.client.get('/display/%s' % j.uid)
        assert "Status of job" in rv.data

    def test_compat_status(self):
        """Test if old-style status urls display the correct results"""
        rv = self.client.get('/status.php?user=invalid')
        self.assert404(rv)
        j = Job()
        self.db.session.add(j)
        self.db.session.commit()
        rv = self.client.get('/status.php?user=%s' % j.uid)
        assert "Status of job" in rv.data

    def test_compat_downloadpage(self):
        """Test if old download page link works"""
        rv = self.client.get('/download.html')
        assert "The current version of antiSMASH is 1.2" in rv.data

    def test_compat_helppage(self):
        """Test if old help page link works"""
        rv = self.client.get('/help.html')
        assert "antiSMASH Help" in rv.data

    def test_compat_aboutpage(self):
        """Test if old about page link works"""
        rv = self.client.get('/about.html')
        assert "About antiSMASH" in rv.data

    def test_compat_contactpage(self):
        """Test if old contact form link works"""
        rv = self.client.get('/contact.html')
        assert "you can contact us with this form" in rv.data

    def test_compat_contactpage_sent_mail(self):
        """Test if contact page reports that it sent a message"""
        data = dict(email="ex@mp.le", body="Test body")
        with websmash.mail.record_messages() as outbox:
            rv = self.client.post('/contact.html', data=data, follow_redirects=True)
            assert "Your message was successfully sent." in rv.data
            assert data['body'] in rv.data
            assert len(outbox) == 2
            contact_msg = outbox[0]
            confirm_msg = outbox[1]
            assert contact_msg.subject == 'antiSMASH feedback'
            assert data['body'] in contact_msg.body
            assert confirm_msg.subject == 'antiSMASH feedback received'
            assert data['body'] in confirm_msg.body