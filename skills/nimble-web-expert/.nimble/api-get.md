```
{
  "name": "amazon_pdp",
  "is_public": true,
  "display_name": "Amazon Product Details Page",
  "description": "The Amazon Product Detail Page Agent extracts structured data from individual product pages on Amazon. This agent is ideal for tracking competitor pricing, monitoring catalog changes, and powering product intelligence use cases.",
  "vertical": "Ecommerce",
  "entity_type": "Product Detail Page (PDP)",
  "domain": "www.amazon.com",
  "managed_by": "nimble",
  "output_schema": {
    "product_title": {
      "type": "string",
      "description": "The name of the product"
    },
    "manufacturer": {
      "type": "string",
      "description": "The company that manufactured the product"
    },
    "product_url": {
      "type": "string",
      "description": "The direct Amazon URL of the product"
    },
    "pack_size": {
      "type": "string",
      "description": "The packaging or pack size information (e.g., 12-pack, 500ml)"
    },
    "web_price": {
      "type": "number",
      "description": "The current selling price of the product in USD"
    },
    "product_detail_column_and_information_within_table": {
      "type": "array",
      "description": "Tabular details about the product such as specifications or attributes",
      "items": {
        "type": "object",
        "properties": {
          "field": {
            "type": "string"
          },
          "value": {
            "type": "string"
          }
        }
      }
    },
    "product_availability_and_delivery_terms": {
      "type": "string",
      "description": "Shipping terms, delivery times, or availability details"
    },
    "unit_of_measure": {
      "type": "string",
      "description": "Unit of measurement for the product (e.g., oz, lb, ml, pack)"
    },
    "unit_of_measure_quantity": {
      "type": "number",
      "description": "Numeric quantity of the product in the specified unit of measure"
    },
    "selection_for_type_of_item_field": {
      "type": "string",
      "description": "Primary selection option field label (e.g., Size, Color)"
    },
    "selection_for_type_of_item_field_entry": {
      "type": "string",
      "description": "The selected value for the primary selection field"
    },
    "secondary_selection_for_type_of_item_field": {
      "type": "string",
      "description": "Secondary selection option field label (if applicable)"
    },
    "secondary_selection_for_type_of_item_field_entry": {
      "type": "string",
      "description": "The selected value for the secondary selection field"
    },
    "list_price": {
      "type": "number",
      "description": "The original price (before discounts) of the product in USD"
    },
    "product_hierarchy": {
      "type": "array",
      "description": "Breadcrumb navigation path or category hierarchy for the product",
      "items": {
        "type": "string"
      }
    },
    "reviews_statistics_percentage_five_to_zero": {
      "type": "object",
      "description": "Distribution of customer ratings (5-star through 0-star)",
      "properties": {
        "5_star": {
          "type": "string"
        },
        "4_star": {
          "type": "string"
        },
        "3_star": {
          "type": "string"
        },
        "2_star": {
          "type": "string"
        },
        "1_star": {
          "type": "string"
        }
      }
    },
    "review_scale": {
      "type": "number",
      "description": "Numerical rating scale used (usually 5)"
    },
    "availability": {
      "type": "boolean",
      "description": "Whether the product is in stock (true) or out of stock (false)"
    },
    "image_url": {
      "type": "string",
      "description": "The URL of the product's main image",
      "format": "uri"
    },
    "brand": {
      "type": "string",
      "description": "The brand name of the product"
    },
    "product_description": {
      "type": "string",
      "description": "Detailed text description of the product"
    },
    "publisher": {
      "type": "string",
      "description": "The publisher, distributor, or entity responsible for listing the product"
    },
    "average_of_reviews": {
      "type": "number",
      "minimum": 0,
      "maximum": 5,
      "description": "The average customer rating (0 to 5 stars)"
    },
    "number_of_reviews": {
      "type": "number",
      "description": "The total number of customer reviews for the product"
    },
    "sold_by": {
      "type": "string",
      "description": "The entity or seller offering the product"
    },
    "direct": {
      "type": "boolean",
      "description": "If seller is Amazon"
    },
    "ships_from": {
      "type": "string",
      "description": "The fulfillment source or warehouse shipping the product"
    },
    "payment": {
      "type": "string",
      "description": "Available payment methods or terms"
    },
    "packaging": {
      "type": "string",
      "description": "Product packaging details (e.g., box, bag, recyclable packaging)"
    },
    "amazons_choice": {
      "type": "boolean",
      "description": "Whether the product is marked as Amazon's Choice"
    },
    "best_sellers_category_1_name": {
      "type": "string",
      "description": "The name of the primary Best Seller category"
    },
    "best_sellers_category_1_rank": {
      "type": "string",
      "description": "The Best Seller rank of the product within the primary category"
    },
    "best_sellers_category_2_name": {
      "type": "string",
      "description": "The name of the secondary Best Seller category"
    },
    "best_sellers_category_2_rank": {
      "type": "string",
      "description": "The Best Seller rank of the product within the secondary category"
    },
    "climate_pledge_friendly": {
      "type": "boolean",
      "description": "Indicates if the product is part of Amazon's Climate Pledge Friendly program"
    },
    "warning": {
      "type": "string",
      "description": "Product warnings (e.g., choking hazard, safety notes)"
    },
    "special_feature": {
      "type": "string",
      "description": "Unique feature or benefit of the product"
    },
    "variants": {
      "type": "array",
      "description": "ASINs of related or variant products (e.g., other colors or sizes)",
      "items": {
        "type": "string"
      }
    },
    "brief_product_description": {
      "type": "array",
      "description": "Bullet-point features or highlights of the product",
      "items": {
        "type": "string"
      }
    },
    "size": {
      "type": "string",
      "description": "Dimensions or size specification (LxWxH)"
    },
    "color": {
      "type": "string",
      "description": "Color of the product"
    },
    "material": {
      "type": "string",
      "description": "Material composition of the product"
    },
    "recommended_uses": {
      "type": "string",
      "description": "Suggested uses or scenarios for the product"
    },
    "model": {
      "type": "string",
      "description": "Manufacturer's model number"
    },
    "country_of_origin": {
      "type": "string",
      "description": "Country where the product was manufactured"
    },
    "asin": {
      "type": "string",
      "description": "Amazon Standard Identification Number (ASIN) of the product"
    },
    "customers_say": {
      "type": "string",
      "description": "AI-generated summary of customer feedback"
    },
    "top_reviews": {
      "type": "array",
      "description": "Top reviews for the product (typically the most helpful or recent ones)",
      "items": {
        "type": "object",
        "properties": {
          "stars": {
            "type": "number"
          },
          "review_title": {
            "type": "string"
          },
          "review_body": {
            "type": "string"
          }
        }
      }
    },
    "technical_details": {
      "type": "array",
      "description": "Technical specifications or details of the product",
      "items": {
        "type": "object",
        "properties": {
          "key": {
            "type": "string"
          },
          "value": {
            "type": "string"
          }
        }
      }
    },
    "brand_logo": {
      "type": "string",
      "description": "URL of the brand's logo"
    },
    "brand_story_background": {
      "type": "string",
      "description": "URL of the background image behind the brand logo"
    },
    "brand_description": {
      "type": "string",
      "description": "Text description of the brand"
    },
    "brand_store": {
      "type": "string",
      "description": "URL of the brand's Amazon store page"
    },
    "bought_in_past_month": {
      "type": "string",
      "description": "Recent sales trends, e.g., number of units bought in the past month"
    },
    "frequently_bought_with": {
      "type": "object",
      "description": "Items that are commonly purchased alongside this product",
      "properties": {
        "total_price": {
          "type": "string"
        },
        "products": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "price": {
                "type": "string"
              },
              "title": {
                "type": "string"
              },
              "asin": {
                "type": "string"
              }
            }
          }
        }
      }
    },
    "long_text": {
      "type": "string"
    },
    "alternatives": {
      "type": "array",
      "description": "Alternative products available on Amazon",
      "items": {
        "type": "object",
        "properties": {
          "asin": {
            "type": "string"
          },
          "price": {
            "type": "string"
          },
          "title": {
            "type": "string"
          }
        }
      }
    },
    "4_stars_and_above": {
      "type": "array",
      "description": "Similar products with ratings of 4 stars or higher",
      "items": {
        "type": "object",
        "properties": {
          "title": {
            "type": "string"
          },
          "price": {
            "type": "string"
          },
          "asin": {
            "type": "string"
          }
        }
      }
    },
    "related_products": {
      "type": "array",
      "description": "Other products related to this item",
      "items": {
        "type": "object",
        "properties": {
          "title": {
            "type": "string"
          },
          "price": {
            "type": "string"
          },
          "asin": {
            "type": "string"
          }
        }
      }
    },
    "related_products_free_delivery": {
      "type": "array",
      "description": "Related products with free delivery eligibility",
      "items": {
        "type": "object",
        "properties": {
          "title": {
            "type": "string"
          },
          "price": {
            "type": "string"
          },
          "asin": {
            "type": "string"
          }
        }
      }
    },
    "alternate_products_for_top_3_alternates": {
      "type": "object",
      "description": "Details about substitute products for top 3 alternates",
      "properties": {
        "product_1_product_description": {
          "type": "string",
          "description": "Title/description text for alternate product #1."
        },
        "product_1_url": {
          "type": "string",
          "description": "Canonical Amazon ASIN URL for product #1 (e.g., https://www.amazon.com/dp/...)."
        },
        "product_1_web_price": {
          "type": "string",
          "description": "Displayed price text for product #1 (as extracted, including currency symbol)."
        },
        "product_1_feature": {
          "type": "string",
          "description": "Feature/attribute name for product #1."
        },
        "product_1_feature_value": {
          "type": "string",
          "description": "Value for the feature/attribute of product #1."
        },
        "product_2_product_description": {
          "type": "string",
          "description": "Title/description text for alternate product #2."
        },
        "product_2_url": {
          "type": "string",
          "description": "Canonical Amazon ASIN URL for product #2 (e.g., https://www.amazon.com/dp/...)."
        },
        "product_2_web_price": {
          "type": "string",
          "description": "Displayed price text for product #2 (as extracted, including currency symbol)."
        },
        "product_2_feature": {
          "type": "string",
          "description": "Feature/attribute name for product #2."
        },
        "product_2_feature_value": {
          "type": "string",
          "description": "Value for the feature/attribute of product #2."
        },
        "product_3_product_description": {
          "type": "string",
          "description": "Title/description text for alternate product #3."
        },
        "product_3_url": {
          "type": "string",
          "description": "Canonical Amazon ASIN URL for product #3 (e.g., https://www.amazon.com/dp/...)."
        },
        "product_3_web_price": {
          "type": "string",
          "description": "Displayed price text for product #3 (as extracted, including currency symbol)."
        },
        "product_3_feature": {
          "type": "string",
          "description": "Feature/attribute name for product #3."
        },
        "product_3_feature_value": {
          "type": "string",
          "description": "Value for the feature/attribute of product #3."
        }
      }
    },
    "alternate_product_1_product_description": {
      "type": "string",
      "description": "Description of the first alternate product"
    },
    "alternate_product_1_product_url": {
      "type": "string",
      "description": "URL of the first alternate product"
    },
    "alternate_product_1_web_price": {
      "type": "string",
      "description": "Price of the first alternate product"
    },
    "alternate_product_1_feature": {
      "type": "string",
      "description": "Highlighted feature of the first alternate product"
    },
    "alternate_product_1_feature_value": {
      "type": "string",
      "description": "Value associated with the feature of the first alternate product"
    },
    "feature": {
      "type": "string",
      "description": "Generic feature name of the product"
    },
    "feature_value": {
      "type": "string",
      "description": "Value corresponding to the generic product feature"
    },
    "UNSPSC": {
      "type": "string",
      "description": "The UNSPSC classification code for the product"
    },
    "agent_zip_code": {
      "type": "string",
      "description": "ZIP code of the responsible shipping agent or warehouse"
    },
    "climate_pledge_certification": {
      "type": "string",
      "description": "Certification name associated with Climate Pledge Friendly"
    },
    "UPC": {
      "type": "string",
      "description": "Universal Product Code (UPC) for the item"
    },
    "shipping_weight": {
      "type": "string",
      "description": "Weight of the product used for shipping calculations"
    },
    "product_dimensions": {
      "type": "string",
      "description": "Dimensions of the product package"
    },
    "suggested_use": {
      "type": "string",
      "description": "Suggested application or use instructions"
    },
    "extra_savings": {
      "type": "string",
      "description": "Additional savings offers available on the product"
    },
    "savings": {
      "type": "string",
      "description": "Current discount or savings on the product"
    },
    "subscribe_and_save": {
      "type": "boolean",
      "description": "Whether Subscribe & Save is available"
    },
    "subscribe_and_save_details": {
      "type": "string",
      "description": "Details about the Subscribe & Save program for this product"
    },
    "buy_x_get_y": {
      "type": "string",
      "description": "Buy-one-get-one or similar promotional offers"
    },
    "has_a_plus_section": {
      "type": "boolean",
      "description": "Whether the product page includes an A+ Content section"
    },
    "a_plus_headers": {
      "type": "array",
      "description": "Headers from A+ content sections",
      "items": {
        "type": "string"
      }
    },
    "scent": {
      "type": "string",
      "description": "Fragrance or scent of the product"
    },
    "cel_widgets": {
      "type": "array",
      "description": "Widgets or modules included on the product detail page",
      "items": {
        "type": "string"
      }
    },
    "subscription_price": {
      "type": "string",
      "description": "Discounted price for subscription orders"
    },
    "visible_images_count": {
      "type": "array",
      "description": "Number and details of visible images on the product page",
      "items": {
        "type": "string"
      }
    },
    "deal_description": {
      "type": "string",
      "description": "Details of any ongoing deals or promotions"
    },
    "sun_protection": {
      "type": "string",
      "description": "Level or type of sun protection (e.g., SPF 30)"
    },
    "bundle_asins": {
      "type": "array",
      "description": "ASINs of items sold together as a bundle",
      "items": {
        "type": "string"
      }
    },
    "video_count": {
      "type": "number",
      "description": "Number of product videos available on the listing"
    },
    "shipping_amount": {
      "type": "string",
      "description": "Shipping cost for the product"
    },
    "reviews_ai_summary": {
      "type": "string",
      "description": "AI-generated summary of customer reviews"
    },
    "review_mentions_with_positive_sentiment": {
      "type": "array",
      "description": "Review mentions categorized with positive sentiment",
      "items": {
        "type": "string"
      }
    },
    "review_mentions_with_neutral_sentiment": {
      "type": "array",
      "description": "Review mentions categorized with neutral sentiment",
      "items": {
        "type": "string"
      }
    },
    "review_mentions_with_negative_sentiment": {
      "type": "array",
      "description": "Review mentions categorized with negative sentiment",
      "items": {
        "type": "string"
      }
    },
    "replenishment_frequency_common": {
      "type": "string",
      "description": "Most common replenishment frequency (e.g., every month)"
    },
    "replenishment_frequency_options": {
      "type": "array",
      "description": "List of available replenishment frequency options",
      "items": {
        "type": "string"
      }
    },
    "option_name": {
      "type": "string",
      "description": "The name of a selectable product option"
    },
    "similar_item": {
      "type": "string",
      "description": "A product identified as similar to this one"
    },
    "sponsored_item": {
      "type": "string",
      "description": "Sponsored product promoted alongside the listing"
    },
    "delivery_time_estimate": {
      "type": "string",
      "description": "Estimated delivery time for the product"
    },
    "variations": {
      "type": "array",
      "description": "Different variations of the product (size, color, etc.)",
      "items": {
        "type": "string"
      }
    },
    "uom": {
      "type": "string",
      "description": "Unit of Measure"
    },
    "uomq": {
      "type": "number",
      "description": "Unit of Measure Quantity"
    },
    "moq": {
      "type": "number",
      "description": "Minimum Order Quantity"
    },
    "moq_price": {
      "type": "string",
      "description": "Minimum Order Quantity Price"
    },
    "shipping_time": {
      "type": "string",
      "description": "Estimated shipping time for the product"
    },
    "store_location": {
      "type": "string",
      "description": "Store location in scrape context."
    },
    "price_per_unit": {
      "type": "number",
      "description": "Price of 1 unit in pack."
    },
    "promos": {
      "type": "array",
      "description": "List of promotional sales and deals"
    },
    "coupons": {
      "type": "array",
      "description": "List of available coupons for this product"
    },
    "badges": {
      "type": "array",
      "description": "List of product badges as displayed below the product title"
    }
  },
  "input_properties": [
    {
      "name": "asin",
      "required": true,
      "type": "string",
      "description": "Product ID",
      "rules": [
        "minLength: 1"
      ],
      "examples": [
        "B0DLKFK6LR",
        "B0177IUSTK",
        "B01N1N64V2",
        "B0B9RTKR72",
        "B0DQYPYVB6",
        "B06XC9321S",
        "B09RX4HKTD",
        "B082T6P545",
        "B08NWK2P1J",
        "B004MFME2G"
      ],
      "default": null
    },
    {
      "name": "zip_code",
      "required": false,
      "type": "string",
      "description": "Zip code for location",
      "rules": [
        "minLength: 1"
      ],
      "examples": null,
      "default": "90210"
    }
  ],
  "feature_flags": {
    "is_localization_supported": true,
    "is_pagination_supported": false
  }
}
```