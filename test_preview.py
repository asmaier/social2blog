import face2blog

import requests
from requests_html import HTMLSession

class TestPreview():

	def test_preview(self):

		session = requests.Session()
		headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36",
		'Referer': 'https://www.google.com'}
		headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_1) AppleWebKit/601.2.4 (KHTML, like Gecko) Version/9.0.1 Safari/601.2.4 facebookexternalhit/1.1 Facebot'} 

		urls = [
			"http://queue.acm.org/detail.cfm?id=2891413",
			"http://chng.it/nfjndtK2js", 
			"https://www.youtube.com/watch?v=Hrqn-ONMrr0",
			"https://hpi-schul-cloud.de/",
			"https://efahrer.chip.de/news/die-ganze-welt-mit-strom-versorgen-forscher-ueberraschen-mit-solardach-rechnung_106186",
			"https://www.zdf.de/dokumentation/zdfinfo-doku/die-sieben-geheimen-atomplaene--der-ddr-100.html",
			"https://www.zdf.de/comedy/die-anstalt/die-anstalt-vom-7-dezember-2021-100.html",
			"https://www.rbb24.de/panorama/beitrag/2022/06/reisen-europa-bahn-bus-auto-flugzeug-co2.html",
			# "https://archive.ph/w9Hn3",
			"https://www.amazon.com/dp/1642507911",
			"https://www.zdf.de/kultur/aspekte/aspekte-russland-exil-102.html",
			"https://www.science.org/content/article/how-far-out-can-we-forecast-weather-scientists-have-new-answer",
			"https://www.fr.de/wirtschaft/sind-wie-in-england-warum-waermepumpen-in-deutschland-dreimal-so-teuer-92401461.html",
			"https://www.blick.ch/ausland/ich-leb-mein-leben-alles-andere-ist-mir-scheissegal-superreiche-lachen-im-privatjet-ueber-klimakleber-id18743116.html"
		]

		for url in urls:
			preview, domain = face2blog._get_preview(url, headers=headers, session=session)
			print(preview.title)
			print(domain)

		session = HTMLSession()
		for url in urls:
			preview, domain = face2blog._get_preview(url, headers=headers, session=session)
			print(preview.title)
			print(preview.description)
			print(domain)