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


def test_extractor_reads_nested_next_data_items():
    html = """
    <html><body>
      <script id="__NEXT_DATA__" type="application/json">
      {"props":{"pageProps":{"state":{"catalog":{"items":[
        {"id":"nd1","url":"https://www.avito.ru/moskva/item","title":"Квартира","price":100}
      ]}}}}}
      </script>
    </body></html>
    """
    listings = AvitoExtractor().extract(html)
    assert len(listings) == 1
    assert listings[0].listing_id == "nd1"
    assert str(listings[0].url).startswith("https://www.avito.ru/")


def test_extractor_normalizes_relative_avito_url_in_next_data():
    html = """
    <html><body>
      <script id="__NEXT_DATA__" type="application/json">
      {"items":[{"id":"rel1","url":"/moskva/kvartiry/test","title":"x","price":1}]}
      </script>
    </body></html>
    """
    listings = AvitoExtractor().extract(html)
    assert len(listings) == 1
    assert str(listings[0].url) == "https://www.avito.ru/moskva/kvartiry/test"


def test_extractor_handles_catalog_items_with_url_path_and_price_detailed():
    html = """
    <html><body>
      <script type="mime/invalid">
      {"state":{"data":{"catalog":{"items":[
        {"id":"x1","urlPath":"/moskva/kvartiry/item","title":"2-к. квартира, 71,2 м², 3/18 эт.","priceDetailed":{"value":86000},"sortTimeStamp":1778155693000,"addressDetailed":{"locationName":"Москва"},"isReserved":true}
      ]}}}}
      </script>
    </body></html>
    """
    listings = AvitoExtractor().extract(html)
    assert len(listings) == 1
    item = listings[0]
    assert item.listing_id == "x1"
    assert str(item.url) == "https://www.avito.ru/moskva/kvartiry/item"
    assert item.price == 86000
    assert item.rooms == 2
    assert item.area == 71.2
    assert item.address == "Москва"
    assert item.is_reserved is True


def test_extractor_normalizes_images_from_dict_entries():
    html = """
    <html><body>
      <script type="mime/invalid">
      {"state":{"data":{"catalog":{"items":[
        {"id":"img1","urlPath":"/moskva/kvartiry/img","title":"1-к. квартира, 35,0 м²","priceDetailed":{"value":1000},"images":[{"318x318":"https://img.example/1.jpg","636x636":"https://img.example/2.jpg"}]}
      ]}}}}
      </script>
    </body></html>
    """
    listings = AvitoExtractor().extract(html)
    assert len(listings) == 1
    assert listings[0].images == ["https://img.example/1.jpg", "https://img.example/2.jpg"]
