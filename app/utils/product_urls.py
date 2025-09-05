"""
Product URL configuration for FreshNutrients products.

This module contains the mapping of product names to their webpage URLs.
For products marked as 'placeholder', the base FreshNutrients URL is used.
"""

# Base URL for FreshNutrients website
FRESHNUTRIENTS_BASE_URL = "https://freshnutrients.org"

# Product name to URL mapping
PRODUCT_URLS = {
    "AfriKelp Plus": "https://www.freshnutrients.org/our-products/afrikelp",
    "AquaMate": FRESHNUTRIENTS_BASE_URL,  # placeholder
    "BlaC-Cal": FRESHNUTRIENTS_BASE_URL,  # placeholder
    "BlaC-Mag": FRESHNUTRIENTS_BASE_URL,  # placeholder
    "BlaC-S": FRESHNUTRIENTS_BASE_URL,  # placeholder
    "Calsap": "https://www.freshnutrients.org/our-products/calsap",
    "FreshBoost": FRESHNUTRIENTS_BASE_URL,  # placeholder (note: original had typo "plceholder")
    "FreshBugs Quorum": "https://www.freshnutrients.org/our-products/freshbugs-quorum",
    "Fresh P": "https://www.freshnutrients.org/our-products/fresh-p",
    "Launch": FRESHNUTRIENTS_BASE_URL,  # placeholder
    "Soft Cal": "https://www.freshnutrients.org/our-products/softcal",
    "Soft Manganese": FRESHNUTRIENTS_BASE_URL,  # placeholder
    "Soft Zinc": "https://www.freshnutrients.org/our-products/soft-zn",
}


def get_product_url(product_name: str) -> str:
    """
    Get the webpage URL for a given product name.
    
    Args:
        product_name: The name of the product
        
    Returns:
        The URL for the product webpage, or base URL if not found
    """
    return PRODUCT_URLS.get(product_name, FRESHNUTRIENTS_BASE_URL)


def add_product_url_to_context(product_context: dict) -> dict:
    """
    Add the product_url field to a product context dictionary.
    
    Args:
        product_context: Dictionary containing product information
        
    Returns:
        Updated dictionary with product_url field added
    """
    if "product_name" in product_context:
        product_context["product_url"] = get_product_url(product_context["product_name"])
    else:
        product_context["product_url"] = FRESHNUTRIENTS_BASE_URL
    
    return product_context


def get_all_product_urls() -> dict:
    """
    Get all configured product URLs.
    
    Returns:
        Dictionary mapping product names to URLs
    """
    return PRODUCT_URLS.copy()
