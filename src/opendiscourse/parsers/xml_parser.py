"""XML parser for GovInfo and Congress.gov XML data."""

import io
from typing import Any, Dict, List, Optional
from lxml import etree


def parse_xml_string(xml_string: str) -> Dict[str, Any]:
    """Parse XML string to dict."""
    root = etree.fromstring(xml_string.encode())
    return _element_to_dict(root)


def parse_xml_file(file_path: str) -> Dict[str, Any]:
    """Parse XML file to dict."""
    with open(file_path, "rb") as f:
        root = etree.parse(f).getroot()
    return _element_to_dict(root)


def _element_to_dict(element) -> Dict[str, Any]:
    """Convert lxml element to dict."""
    result = {}
    for key, val in element.attrib.items():
        result[f"@{key}"] = val
    children = list(element)
    if children:
        for child in children:
            child_dict = _element_to_dict(child)
            tag = child.tag
            if tag in result:
                if not isinstance(result[tag], list):
                    result[tag] = [result[tag]]
                result[tag].append(child_dict)
            else:
                result[tag] = child_dict
    elif element.text and element.text.strip():
        text = element.text.strip()
        if result:
            result["#text"] = text
        else:
            return text
    return result


def extract_text_elements(root, xpath: str) -> List[str]:
    """Extract text from all elements matching xpath."""
    elements = root.xpath(xpath)
    return [el.text.strip() for el in elements if el.text and el.text.strip()]
