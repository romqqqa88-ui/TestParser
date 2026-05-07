from avito_parser_console.parser.avito_extractor import AvitoExtractor


def test_extractor_reads_mime_invalid_json_items():
    html = """
    <html><body>
      <script type="mime/invalid">
      {"items":[{"id":"1","url":"https://www.avito.ru/item1","title":"Квартира","price":10000000}]}
      </script>
    </body></html>
    """
    listings = AvitoExtractor().extract(html)
    assert len(listings) == 1
    assert listings[0].listing_id == "1"


def test_extractor_falls_back_to_untyped_script_with_items():
    html = """
    <html><body>
      <script>
      window.__initialData={"items":[{"id":"fb1","url":"https://www.avito.ru/i","title":"x","price":1}]};
      </script>
    </body></html>
    """
    listings = AvitoExtractor().extract(html)
    assert len(listings) == 1
    assert listings[0].listing_id == "fb1"
