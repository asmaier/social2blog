import face2blog

import requests
from requests_html import HTMLSession
import linkpreview

import json
import codecs

class TestPreview():

	def test_preview(self):

		session = requests.Session()
		headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36",
		'Referer': 'https://www.google.com'}
		headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_1) AppleWebKit/601.2.4 (KHTML, like Gecko) Version/9.0.1 Safari/601.2.4 facebookexternalhit/1.1 Facebot'} 

		urls = [
			"http://www.heise.de/open/meldung/Deutschlands-erstes-Portal-fuer-offene-Daten-in-Berlin-1558417.html",
			"http://www.pro-physik.de/details/physiknews/10818800/Europas_Weg_zum_High-Performer.html",
			"https://www.rbb24.de/panorama/thema/wiegehtesuns/russin-berlin-krieg-ukraine-propaganda-familie-.html",
			"http://www.golem.de/0806/60182.html",
			"https://redmine.piratenfraktion-berlin.de/issues/131",
			"http://queue.acm.org/detail.cfm?id=2891413",
			"http://chng.it/nfjndtK2js", 
			"https://www.youtube.com/watch?v=Hrqn-ONMrr0",
			"https://hpi-schul-cloud.de/",
			"https://efahrer.chip.de/news/die-ganze-welt-mit-strom-versorgen-forscher-ueberraschen-mit-solardach-rechnung_106186",
			"https://www.zdf.de/dokumentation/zdfinfo-doku/die-sieben-geheimen-atomplaene--der-ddr-100.html",
			"https://www.zdf.de/comedy/die-anstalt/die-anstalt-vom-7-dezember-2021-100.html",
			"https://www.rbb24.de/panorama/beitrag/2022/06/reisen-europa-bahn-bus-auto-flugzeug-co2.html",
			"https://archive.ph/w9Hn3",
			"https://www.amazon.com/dp/1642507911",
			"https://www.zdf.de/kultur/aspekte/aspekte-russland-exil-102.html",
			"https://www.science.org/content/article/how-far-out-can-we-forecast-weather-scientists-have-new-answer",
			"https://www.fr.de/wirtschaft/sind-wie-in-england-warum-waermepumpen-in-deutschland-dreimal-so-teuer-92401461.html",
			"https://www.blick.ch/ausland/ich-leb-mein-leben-alles-andere-ist-mir-scheissegal-superreiche-lachen-im-privatjet-ueber-klimakleber-id18743116.html"
		]

		# HTMLSession is better, but unfortunately not thread safe
		# session = HTMLSession()
		for index, url in enumerate(urls):
			try:
				preview, domain = face2blog._get_preview(url, headers=headers, session=session)
				print("Title:", preview.title)
				print("Image:", preview.absolute_image)
				print("Domain:", domain)

				if face2blog._is_url(preview.absolute_image):
					r = requests.get(preview.absolute_image)
					print("Preview image field is an url to a valid an image:", face2blog._is_image(r.content))
				else:
					print("Preview image field is not an url.")
			except (requests.exceptions.RequestException, linkpreview.exceptions.LinkPreviewException, AttributeError) as err:
				print(f"Post number {index}", url)
				print(f"Post number {index}", err)

			print("------")

	def test_process_post(self):

		# this must be a raw string so line breaks are preserved and \n chars are allowed
		json_string = r'''[
				{
			"timestamp": 1321869323,
			"attachments": [
			  {
				"data": [
				  {
					"external_context": {
					  "url": "https://redmine.piratenfraktion-berlin.de/issues/131"
					}
				  }
				]
			  }
			],
			"data": [
			  {
				"post": "Auszug aus einem Antrag der Piraten an den Berliner Innensenat:\n\n\"Die Piratenfraktion im Abgeordnetenhaus von Berlin verzichtet auf den ihr zustehenden Dienstwagen und bittet Sie um die einmalige Anschaffung von 15 Fahrr\u00c3\u00a4dern im Wert von je maximal 2000,- Euro sowie die j\u00c3\u00a4hrliche Anschaffung von 15 VBB-Umweltkarten Berlin ABC f\u00c3\u00bcr die Mitglieder der Piratenfraktion.\n\nBegr\u00c3\u00bcndung:\n\nNach \u00c2\u00a7 8 Abs. 5 des Fraktionsgesetzes stehen der Piratenfraktion Sachleistungen zu. Zu diesen Sachleistungen geh\u00c3\u00b6rt unter anderem ein Dienstwagen mit personengebundenem Fahrer f\u00c3\u00bcr den Fraktionsvorsitzenden. Wagen und Fahrer belasten den Haushalt von Berlin zur Zeit mit j\u00c3\u00a4hrlich 93.028,- Euro (Drs. 16/4411). Im Falle der Nutzung durch die Piratenfraktion w\u00c3\u00bcrden der Stadt Berlin somit f\u00c3\u00bcr die 17. Wahlperiode Kosten in H\u00c3\u00b6he von ca. 465.190,- Euro entstehen.\n\nDurch die einmalige Anschaffung von 15 Fahrr\u00c3\u00a4dern im Wert von je maximal 2.000,- Euro entstehen der Stadt Berlin einmalig Kosten in H\u00c3\u00b6he von 30.000,- Euro. Ich stelle anheim, ob die Fahrr\u00c3\u00a4der in den Fuhrpark des Landes Berlin \u00c3\u00bcbernommen werden, oder nach Anschaffung in das Eigentum der Fraktionsmitglieder \u00c3\u00bcbergehen sollen.\n\nDie j\u00c3\u00a4hrlichen Kosten f\u00c3\u00bcr 15 VBB-Umweltkarten Berlin ABC betragen 13.125,- Euro. Auf einen Zeitraum von f\u00c3\u00bcnf Jahren gerechnet entstehen Kosten in H\u00c3\u00b6he von ca. 65.625,- Euro.\n\nMit unserem L\u00c3\u00b6sungsvorschlag w\u00c3\u00bcrde das Land Berlin f\u00c3\u00bcr die Dauer der 17. Wahlperiode 369.565,- Euro einsparen.\""
			  },
			  {
				"update_timestamp": 1321869323
			  },
			  {
				
			  },
			  {
				
			  }
			],
			"title": "Andreas Maier hat einen Link geteilt."
		  },
		  {
			"timestamp": 1297719858,
			"attachments": [
			  {
				"data": [
				  {
					"external_context": {
					  "url": "http://www.faceresearch.org/demos/average"
					}
				  }
				]
			  }
			],
			"data": [
			  {
				"post": "Wie sieht wohl das durchschnittliche Facebook-Gesicht aus?"
			  },
			  {
				"update_timestamp": 1297719858
			  },
			  {
				
			  },
			  {
				
			  }
			],
			"title": "Andreas Maier hat einen Link geteilt."
		  },
			{
			"timestamp": 1331717686,
			"attachments": [
			  {
				"data": [
				  {
					"external_context": {
					  "url": "http://zimory.de/index.php?id=116&L=0"
					}
				  }
				]
			  }
			],
			"data": [
			  {
				"update_timestamp": 1331717686
			  },
			  {
				
			  },
			  {
				
			  }
			],
			"title": "Andreas Maier hat einen Link geteilt."
		  },
			{
			"timestamp": 1403089908,
			"attachments": [
			  {
				"data": [
				  {
					"external_context": {
					  "url": "http://www.infranken.de/regional/coburg/Wildpark-Schloss-Tambach-soll-Ende-des-Jahres-schliessen;art214,733719"
					}
				  }
				]
			  }
			],
			"data": [
			  {
				"update_timestamp": 1403089908
			  },
			  {
				
			  },
			  {
				
			  }
			],
			"title": "Andreas Maier hat einen Link geteilt."
		  },
			{
			"timestamp": 1605703213,
			"attachments": [
			  {
				"data": [
				  {
					"external_context": {
					  "url": "https://www.paketda.de/news-ruecksendungen-russland.html"
					}
				  }
				]
			  }
			],
			"data": [
			  {
				"post": "Liebe DHL, seit Monaten werden von ihnen Pakete aus Russland ohne Erkl\u00c3\u00a4rung zur\u00c3\u00bcckgeschickt. Auf telefonische Nachfragen nach dem Grund gibt es keine Erkl\u00c3\u00a4rung. Daher meine Frage: K\u00c3\u00b6nnen sie die Vermutung von https://www.paketda.de/news-ruecksendungen-russland.html best\u00c3\u00a4tigen, dass sie die Pakete deswegen zur\u00c3\u00bcckschicken, weil an den Paketen keine ausgedruckte CN22/23-Formulare h\u00c3\u00a4ngen, sie aber gleichzeitig keine digitalen Zolldaten akzeptieren? Und wieso wird dieses Problem nicht mit Dringlichkeit an die russische Post kommuniziert? Und warum bekommt man als Kunde keine Erkl\u00c3\u00a4rung von ihnen und ist stattdessen auf Ger\u00c3\u00bcchte von anderen Webseiten angewiesen? Wie lange soll dieser Zustand noch so bleiben? Ist ihnen klar, dass durch Corona sehr viele Familien von ihren Verwandten in Russland derzeit abgeschnitten sind und sie durch ihre Unt\u00c3\u00a4tigkeit in der Sache jetzt noch nicht einmal Pakete zu Weihnachten und Neujahr empfangen werden k\u00c3\u00b6nnen?"
			  },
			  {
				"update_timestamp": 1605703213
			  }
			]
		  }
		]  
		'''

		# Thanks to codeium for pointing to codecs library
		# raw_unicode_escape will leave the \n linebreaks untouched
		string_fixed = codecs.decode(json_string, 'raw_unicode_escape').encode('latin-1').decode('utf-8')
		# we need strict=False to allow linebreaks \n in json strings
		# see https://stackoverflow.com/questions/22394235/invalid-control-character-with-python-json-loads

		posts = json.loads(string_fixed, strict=False)

		for index, post in enumerate(posts):
			result = face2blog._process_post(post, index)
			print("title", result[0])
			print("datetime", result[1])
			print("content", result[2])
			print("image url", result[3])



