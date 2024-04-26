import random

import requests
from lxml import etree

headers = {
	"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}


def get_random_image_from_web (output_location: str) -> None:
	"""
	Gets a random image from the artistic/anime category on besthdwallpaper.com.
	:param output_location: The path to save the downloaded image to
	:return: None
	"""
	# Get page information
	page_info: dict[str, any] = requests.get \
		("https://www.besthdwallpaper.com/anime-wallpapers-ct_en-US-51/1?isJson=true",
		 headers = headers).json()["psf"]

	last_page = page_info["pageCount"]

	# Loop until we successfully get an image
	got_image = False

	while not got_image:
		# Pick a random page
		page_number = random.randint(1, last_page)

		# Download page JSON
		page_data: list[dict[str, any]] = requests.get \
			(f"https://www.besthdwallpaper.com/anime-wallpapers-ct_en-US-51/{page_number}?isJson=true",
			 headers = headers).json()["data"]

		# Pick random image
		image_info: dict[str, any] = random.choice(page_data)

		# Check if image meets conditions
		# noinspection PyChainedComparisons
		if not image_info["isOver18"] and \
				image_info["imWidth"] >= 3840 and \
				image_info["imHeight"] >= 2160 and \
				image_info["imWidth"] >= image_info["imHeight"]:
			# Get image details page
			image_details = requests.get(f"https://www.besthdwallpaper.com{image_info['detailPageUrl']}",
										 headers = headers)

			# Get link to image
			# noinspection PyProtectedMember
			elements: list[etree._Element] = etree.HTML(image_details.text).xpath('//a[text()=" 3840x2160 "]')
			if len(elements) != 0:
				image_url: str = elements[0].attrib["href"]

				# Check if image is a jpeg
				if image_url.endswith(".jpg") or image_url.endswith(".jpeg") or image_url.endswith(".jpe") or \
						image_url.endswith(".jif") or image_url.endswith(".jfif") or image_url.endswith(".jfi"):
					# Download file
					with open(output_location, "wb") as output_file:
						output_file.write(requests.get(image_url, headers = headers).content)

					# Finish loop
					got_image = True


if __name__ == "__main__":
	get_random_image_from_web(output_location = r"C:\Users\ajdmi\PycharmProjects\nnc_automaton\data\test.jpg")
