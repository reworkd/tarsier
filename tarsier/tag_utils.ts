// noinspection JSUnusedGlobalSymbols
interface Window {
  // Playwright's .evaluate method runs javascript code in an isolated scope.
  // This means that subsequent calls to .evaluate will not have access to the functions defined in this file
  // since they will be in an inaccessible scope. To circumvent this, we attach the following methods to the
  // window which is always available globally when run in a browser environment.
  tagifyWebpage: (tagLeafTexts?: boolean) => TagMetadata[];
  removeTags: () => void;
  hideNonTagElements: () => void;
  revertVisibilities: () => void;
  fixNamespaces: (tagName: string) => string;
}

interface TagMetadata {
  tarsierId: number;
  elementName: string;
  openingTagHTML: string;
  xpath: string;
  elementText: string | null;
  textNodeIndex?: number | null; // Used if the tag refers to specific TextNode elements within the tagged ElementNode
  idSymbol: string;
  idString: string;
}

const tarsierId = "__tarsier_id";
const tarsierDataAttribute = "data-tarsier-id";
const tarsierSelector = `#${tarsierId}`;
const reworkdVisibilityAttribute = "reworkd-original-visibility";
type TagSymbol = "#" | "$" | "@" | "%" | "";

const elIsVisible = (el: HTMLElement) => {
  const rect = el.getBoundingClientRect();
  const computedStyle = window.getComputedStyle(el);

  const isHidden =
    computedStyle.visibility === "hidden" ||
    computedStyle.display === "none" ||
    el.hidden ||
    (el.hasAttribute("disabled") && el.getAttribute("disabled"));

  const has0Opacity = computedStyle.opacity === "0";
  // Often input elements will have 0 opacity but still have some interactable component
  const isTransparent = has0Opacity && !hasLabel(el);
  const isDisplayContents = computedStyle.display === "contents";
  const isZeroSize =
    (rect.width === 0 || rect.height === 0) && !isDisplayContents; // display: contents elements have 0 width and height
  const isScriptOrStyle = el.tagName === "SCRIPT" || el.tagName === "STYLE";
  return !isHidden && !isTransparent && !isZeroSize && !isScriptOrStyle;
};

function hasLabel(element: HTMLElement): boolean {
  const tagsThatCanHaveLabels = ["input", "textarea", "select", "button"];

  if (!tagsThatCanHaveLabels.includes(element.tagName.toLowerCase())) {
    return false;
  }

  const escapedId = CSS.escape(element.id);
  const label = document.querySelector(`label[for="${escapedId}"]`);

  if (label) {
    return true;
  }

  // The label may not be directly associated with the element but may be a sibling
  const siblings = Array.from(element.parentElement?.children || []);
  for (let sibling of siblings) {
    if (sibling.tagName.toLowerCase() === "label") {
      return true;
    }
  }

  return false;
}

const isTaggableTextNode = (child: ChildNode) => {
  return isNonWhiteSpaceTextNode(child) && isTextNodeAValidWord(child);
};

const isNonWhiteSpaceTextNode = (child: ChildNode) => {
  return (
    child.nodeType === Node.TEXT_NODE &&
    child.textContent &&
    child.textContent.trim().length > 0 &&
    child.textContent.trim() !== "\u200B"
  );
};

const isTextNodeAValidWord = (child: ChildNode) => {
  // We don't want to be tagging separator symbols like '|' or '/' or '>' etc
  const trimmedWord = child.textContent?.trim();
  return trimmedWord && (trimmedWord.match(/\w/) || trimmedWord.length > 3); // Regex matches any character, number, or _
};

const isImageElement = (el: HTMLElement) => {
  return el.tagName.toLowerCase() === "img";
};

const inputs = ["a", "button", "textarea", "select", "details", "label"];
const isInteractable = (el: HTMLElement) => {
  // If it is a label but has an input child that it is a label for, say not interactable
  if (el.tagName.toLowerCase() === "label" && el.querySelector("input")) {
    return false;
  }

  return (
    inputs.includes(el.tagName.toLowerCase()) ||
    // @ts-ignore
    (el.tagName.toLowerCase() === "input" && el.type !== "hidden") ||
    el.role === "button"
  );
};

const text_input_types = [
  "text",
  "password",
  "email",
  "search",
  "url",
  "tel",
  "number",
];
const isTextInsertable = (el: HTMLElement) =>
  el.tagName.toLowerCase() === "textarea" ||
  (el.tagName.toLowerCase() === "input" &&
    text_input_types.includes((el as HTMLInputElement).type));

// These tags may not have text but can still be interactable
const textLessTagWhiteList = ["input", "textarea", "select", "button", "a"];

const isTextLess = (el: HTMLElement) => {
  const tagName = el.tagName.toLowerCase();
  if (textLessTagWhiteList.includes(tagName)) return false;
  if (el.childElementCount > 0) return false;
  if ("innerText" in el && el.innerText.trim().length === 0) {
    // look for svg or img in the element
    const svg = el.querySelector("svg");
    const img = el.querySelector("img");

    if (svg || img) return false;

    return isElementInViewport(el);
  }

  return false;
};

function isElementInViewport(el: HTMLElement) {
  const rect = el.getBoundingClientRect();

  const isLargerThan1x1 = rect.width > 1 || rect.height > 1;

  let body = document.body,
    html = document.documentElement;
  const height = Math.max(
    body.scrollHeight,
    body.offsetHeight,
    html.clientHeight,
    html.scrollHeight,
    html.offsetHeight,
  );
  const width = Math.max(
    body.scrollWidth,
    body.offsetWidth,
    html.clientWidth,
    html.scrollWidth,
    html.offsetWidth,
  );

  return (
    isLargerThan1x1 &&
    rect.top >= 0 &&
    rect.left >= 0 &&
    rect.bottom <= height &&
    rect.right <= width
  );
}

function getElementXPath(element: HTMLElement | null) {
  let path_parts = [];

  let iframe_str = "";
  if (element && element.ownerDocument !== window.document) {
    // assert element.iframe_index !== undefined, "Element is not in the main document and does not have an iframe_index attribute";
    iframe_str = `iframe[${element.getAttribute("iframe_index")}]`;
  }

  while (element) {
    if (!element.tagName) {
      element = element.parentNode as HTMLElement | null;
      continue;
    }

    let tagName = element.tagName.toLowerCase();

    let prefix = window.fixNamespaces(tagName);

    let sibling_index = 1;

    let sibling = element.previousElementSibling;
    while (sibling) {
      if (sibling.tagName === element.tagName && sibling.id != tarsierId) {
        sibling_index++;
      }
      sibling = sibling.previousElementSibling;
    }

    // Check next siblings to determine if index should be added
    let nextSibling = element.nextElementSibling;
    let shouldAddIndex = false;
    while (nextSibling) {
      if (nextSibling.tagName === element.tagName) {
        shouldAddIndex = true;
        break;
      }
      nextSibling = nextSibling.nextElementSibling;
    }

    if (sibling_index > 1 || shouldAddIndex) {
      prefix += `[${sibling_index}]`;
    }

    if (element.id) {
      prefix += `[@id="${element.id}"]`;
    } else if (element.className) {
      prefix += `[@class="${element.className}"]`;
    }

    path_parts.unshift(prefix);
    element = element.parentNode as HTMLElement | null;
  }
  return iframe_str + "//" + path_parts.join("/");
}

function create_tagged_span(idNum: number, symbol: TagSymbol) {
  let idStr: string = `[${symbol}${idNum}]`;

  let idSpan = document.createElement("span");
  idSpan.id = tarsierId;
  idSpan.style.position = "relative";
  idSpan.style.display = "inline";
  idSpan.style.color = "white";
  idSpan.style.backgroundColor = "red";
  idSpan.style.padding = "1.5px";
  idSpan.style.borderRadius = "3px";
  idSpan.style.fontWeight = "bold";
  // idSpan.style.fontSize = "15px"; // Removing because OCR won't see small text among large font
  idSpan.style.fontFamily = "Arial";
  idSpan.style.margin = "1px";
  idSpan.style.lineHeight = "1.25";
  idSpan.style.letterSpacing = "2px";
  idSpan.style.zIndex = "2140000046";
  idSpan.style.clip = "auto";
  idSpan.style.height = "fit-content";
  idSpan.style.width = "fit-content";
  idSpan.style.minHeight = "15px";
  idSpan.style.minWidth = "23px";
  idSpan.style.maxHeight = "unset";
  idSpan.style.maxWidth = "unset";
  idSpan.textContent = idStr;
  idSpan.style.webkitTextFillColor = "white";
  idSpan.style.textShadow = "";
  idSpan.style.textDecoration = "none";
  idSpan.style.letterSpacing = "0px";

  idSpan.setAttribute(tarsierDataAttribute, idNum.toString());

  return idSpan;
}

const MIN_FONT_SIZE = 11;
const ensureMinimumTagFontSizes = () => {
  const tags = Array.from(
    document.querySelectorAll(tarsierSelector),
  ) as HTMLElement[];
  tags.forEach((tag) => {
    let fontSize = parseFloat(
      window.getComputedStyle(tag).fontSize.split("px")[0],
    );
    if (fontSize < MIN_FONT_SIZE) {
      tag.style.fontSize = `${MIN_FONT_SIZE}px`;
    }
  });
};

window.tagifyWebpage = (tagLeafTexts = false) => {
  window.removeTags();
  hideMapElements();

  const allElements = getAllElementsInAllFrames();
  const rawElementsToTag = getElementsToTag(allElements, tagLeafTexts);
  const elementsToTag = removeNestedTags(rawElementsToTag);
  const tagMetadataList = insertTags(elementsToTag, tagLeafTexts);
  shrinkCollidingTags();
  ensureMinimumTagFontSizes();

  return tagMetadataList;
};

function getAllElementsInAllFrames(): HTMLElement[] {
  // Main page
  const allElements: HTMLElement[] = Array.from(
    document.body.querySelectorAll("*"),
  );

  // Add all elements in iframes
  // NOTE: This still doesn't work for all iframes
  const iframes = document.getElementsByTagName("iframe");
  for (let i = 0; i < iframes.length; i++) {
    try {
      const frame = iframes[i];
      const iframeDocument =
        frame.contentDocument || frame.contentWindow?.document;
      if (!iframeDocument) continue;

      const iframeElements = Array.from(
        iframeDocument.querySelectorAll("*"),
      ) as HTMLElement[];
      iframeElements.forEach((el) =>
        el.setAttribute("iframe_index", i.toString()),
      );
      allElements.push(...iframeElements);
    } catch (e) {
      console.error("Error accessing iframe content:", e);
    }
  }

  return allElements;
}

function getElementsToTag(
  allElements: HTMLElement[],
  tagLeafTexts: boolean,
): HTMLElement[] {
  const elementsToTag: HTMLElement[] = [];

  for (let el of allElements) {
    if ((isTextLess(el) && !isImageElement(el)) || !elIsVisible(el)) {
      continue;
    }

    if (isInteractable(el) || isImageElement(el)) {
      elementsToTag.push(el);
    } else if (tagLeafTexts) {
      // Append the parent tag as it may have multiple individual child nodes with text
      // We will tag them individually later
      if (Array.from(el.childNodes).filter(isTaggableTextNode).length >= 1) {
        elementsToTag.push(el);
      }
    }
  }

  return elementsToTag;
}

function removeNestedTags(elementsToTag: HTMLElement[]): HTMLElement[] {
  // An interactable element may have multiple tagged elements inside
  // Most commonly, the text will be tagged alongside the interactable element
  // In this case there is only one child, and we should remove this nested tag
  // In other cases, we will allow for the nested tagging

  const res = [...elementsToTag];
  elementsToTag.map((el) => {
    // Only interactable elements can have nested tags
    if (isInteractable(el)) {
      const elementsToRemove: HTMLElement[] = [];
      el.querySelectorAll("*").forEach((child) => {
        const index = res.indexOf(child as HTMLElement);
        if (index > -1) {
          elementsToRemove.push(child as HTMLElement);
        }
      });

      // Only remove nested tags if there is only a single element to remove
      if (elementsToRemove.length <= 2) {
        for (let element of elementsToRemove) {
          res.splice(res.indexOf(element), 1);
        }
      }
    }
  });

  return res;
}

function getTagSymbol(el: HTMLElement): TagSymbol {
  if (isInteractable(el)) {
    if (isTextInsertable(el)) {
      return "#";
    } else if (el.tagName.toLowerCase() === "a") {
      return "@";
    } else {
      return "$";
    }
  } else if (isImageElement(el)) {
    return "%";
  } else {
    return "";
  }
}

function insertTags(
  elementsToTag: HTMLElement[],
  tagLeafTexts: boolean,
): TagMetadata[] {
  function trimTextNodeStart(element: HTMLElement) {
    // Trim leading whitespace from the element's text content
    // This way, the tag will be inline with the word and not textwrap
    // Element text
    if (!element.firstChild || element.firstChild.nodeType !== Node.TEXT_NODE) {
      return;
    }
    const textNode = element.firstChild as Text;
    textNode.textContent = textNode.textContent!.trimStart();
  }

  function getElementToInsertInto(element: HTMLElement): HTMLElement {
    // An <a> tag may just be a wrapper over many elements. (Think an <a> with a <span> and another <span>
    // If these sub children are the only children, they might have styling that mis-positions the tag we're attempting to
    // insert. Because of this, we should drill down among these single children to insert this tag

    // Some elements might just be empty. They should not count as "children" and if there are candidates to drill down
    // into when these empty elements are considered, we should drill
    const childrenToConsider = Array.from(element.childNodes).filter(
      (child) => {
        if (isNonWhiteSpaceTextNode(child)) {
          return true;
        } else if (child.nodeType === Node.TEXT_NODE) {
          return false;
        }

        return !(
          child.nodeType === Node.ELEMENT_NODE &&
          (isTextLess(child as HTMLElement) ||
            !elIsVisible(child as HTMLElement))
        );
      },
    );

    if (childrenToConsider.length === 1) {
      const child = childrenToConsider[0];
      // Also check its a span or P tag
      const elementsToDrillDown = [
        "div",
        "span",
        "p",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
      ];
      if (
        child.nodeType === Node.ELEMENT_NODE &&
        elementsToDrillDown.includes(
          (child as HTMLElement).tagName.toLowerCase(),
        )
      ) {
        return getElementToInsertInto(child as HTMLElement);
      }
    }

    trimTextNodeStart(element);
    return element;
  }

  function getOpeningTag(el: HTMLElement): string {
    const elementWithoutChildren = el.cloneNode(false) as HTMLElement;
    const openingAndClosingTags = elementWithoutChildren.outerHTML;
    const tagName = elementWithoutChildren.tagName.toLowerCase();
    const closingTag = `</${tagName}>`;

    return openingAndClosingTags.endsWith(closingTag)
      ? openingAndClosingTags.slice(0, -closingTag.length)
      : openingAndClosingTags;
  }

  const tagDataList: {
    xpath: string;
    element: HTMLElement;
    tagElement: HTMLElement;
    textNodeIndex: number | null;
    originalTextContent: string | null;
  }[] = [];
  let idNum = 0;

  function createAndInsertTag(
    el: HTMLElement,
    xpath: string,
    textNodeIndex: number | null,
    isAbsolutelyPositioned: boolean,
    referenceNode: ChildNode | null = null,
    originalTextContent: string | null = null,
  ) {
    const symbol = getTagSymbol(el);
    const idSpan = create_tagged_span(idNum, symbol);

    const tagDataEntry = {
      xpath,
      element: el,
      tagElement: idSpan,
      textNodeIndex,
      originalTextContent,
    };

    if (referenceNode && el.parentElement) {
      el.insertBefore(idSpan, referenceNode);
    } else if (isTextInsertable(el) && el.parentElement) {
      el.parentElement.insertBefore(idSpan, el);
    } else {
      const insertionElement = getElementToInsertInto(el);
      insertionElement.prepend(idSpan);
      if (isAbsolutelyPositioned) {
        absolutelyPositionTagIfMisaligned(idSpan, insertionElement);
      }
    }

    if (isAbsolutelyPositioned && !referenceNode) {
      absolutelyPositionTagIfMisaligned(idSpan, el);
    }

    return tagDataEntry;
  }

  for (const el of elementsToTag) {
    const xpath = getElementXPath(el);

    if (isInteractable(el) || isImageElement(el)) {
      const isAbsolutelyPositioned =
        !isTextInsertable(el) || isImageElement(el);

      const originalTextContent = el.textContent?.trim() || null;

      const tagDataEntry = createAndInsertTag(
        el,
        xpath,
        null,
        isAbsolutelyPositioned,
        null,
        originalTextContent,
      );

      tagDataList.push(tagDataEntry);
      idNum++;
    } else if (tagLeafTexts) {
      trimTextNodeStart(el);
      const textNodes = Array.from(el.childNodes).filter(
        (child) => child.nodeType === Node.TEXT_NODE,
      );
      const validTextNodes = textNodes.filter(isTaggableTextNode);

      validTextNodes.forEach((child) => {
        const textNodeIndex = textNodes.indexOf(child) + 1;

        const originalTextContent = child.textContent?.trim() || null;

        const tagDataEntry = createAndInsertTag(
          el,
          xpath,
          textNodeIndex,
          false,
          child,
          originalTextContent,
        );

        tagDataList.push(tagDataEntry);
        idNum++;
      });
    }
  }

  return tagDataList.map((tagData, index) => {
    const elementHTML = getOpeningTag(tagData.element);
    const symbol = getTagSymbol(tagData.element) || "";
    const idString = `[ ${symbol}${symbol ? " " : ""}${index} ]`;

    const elementText = tagData.originalTextContent;

    return {
      tarsierId: index,
      elementName: tagData.element.tagName.toLowerCase(),
      openingTagHTML: elementHTML,
      xpath: tagData.xpath,
      elementText: elementText,
      textNodeIndex: tagData.textNodeIndex,
      idSymbol: symbol,
      idString: idString,
    };
  });
}

function absolutelyPositionTagIfMisaligned(
  tag: HTMLElement,
  reference: HTMLElement,
) {
  /*
  Some tags don't get displayed on the page properly
  This occurs if the parent element children are disjointed from the parent
  In this case, we absolutely position the tag to the parent element
  */

  let tagRect = tag.getBoundingClientRect();
  if (!(tagRect.width === 0 || tagRect.height === 0)) {
    return;
  }

  const distanceThreshold = 250;

  // Check if the expected position is off-screen horizontally
  const expectedTagPositionRect = reference.getBoundingClientRect();
  if (
    expectedTagPositionRect.right < 0 ||
    expectedTagPositionRect.left >
      (window.innerWidth || document.documentElement.clientWidth)
  ) {
    // Expected position is off-screen horizontally, remove the tag
    tag.remove();
    return; // Skip to the next tag
  }

  const referenceTopLeft = {
    x: expectedTagPositionRect.left,
    y: expectedTagPositionRect.top,
  };

  const tagCenter = {
    x: (tagRect.left + tagRect.right) / 2,
    y: (tagRect.top + tagRect.bottom) / 2,
  };

  const dx = Math.abs(referenceTopLeft.x - tagCenter.x);
  const dy = Math.abs(referenceTopLeft.y - tagCenter.y);
  if (dx > distanceThreshold || dy > distanceThreshold || !elIsVisible(tag)) {
    tag.style.position = "absolute";

    // Ensure the tag is positioned within the screen bounds
    let leftPosition = Math.max(
      0,
      expectedTagPositionRect.left - (tagRect.right + 3 - tagRect.left),
    );
    leftPosition = Math.min(
      leftPosition,
      window.innerWidth - (tagRect.right - tagRect.left),
    );
    let topPosition = Math.max(0, expectedTagPositionRect.top + 3); // Add some top buffer to center align better
    topPosition = Math.min(
      topPosition,
      Math.max(window.innerHeight, document.documentElement.scrollHeight) -
        (tagRect.bottom - tagRect.top),
    );

    tag.style.left = `${leftPosition}px`;
    tag.style.top = `${topPosition}px`;

    tag.parentElement && tag.parentElement.removeChild(tag);
    document.body.appendChild(tag);
  }
}

const shrinkCollidingTags = () => {
  const tags = Array.from(
    document.querySelectorAll(tarsierSelector),
  ) as HTMLElement[];
  for (let i = 0; i < tags.length; i++) {
    const tag = tags[i];
    let tagRect = tag.getBoundingClientRect();
    let fontSize = parseFloat(
      window.getComputedStyle(tag).fontSize.split("px")[0],
    );

    for (let j = i + 1; j < tags.length; j++) {
      const otherTag = tags[j];
      let otherTagRect = otherTag.getBoundingClientRect();
      let otherFontSize = parseFloat(
        window.getComputedStyle(otherTag).fontSize.split("px")[0],
      );

      while (
        tagRect.left < otherTagRect.right &&
        tagRect.right > otherTagRect.left &&
        tagRect.top < otherTagRect.bottom &&
        tagRect.bottom > otherTagRect.top &&
        fontSize > MIN_FONT_SIZE &&
        otherFontSize > MIN_FONT_SIZE
      ) {
        fontSize -= 0.5;
        otherFontSize -= 0.5;
        tag.style.fontSize = `${fontSize}px`;
        otherTag.style.fontSize = `${otherFontSize}px`;

        tagRect = tag.getBoundingClientRect();
        otherTagRect = otherTag.getBoundingClientRect();
      }
    }
  }
};

window.removeTags = () => {
  getAllElementsInAllFrames()
    .filter((element) => element.matches(tarsierSelector))
    .forEach((tag) => tag.remove());

  showMapElements();
};

const GOOGLE_MAPS_OPACITY_CONTROL = "__reworkd_google_maps_opacity";

const hideMapElements = (): void => {
  // Maps have lots of tiny buttons that need to be tagged
  // They also have a lot of tiny text and are annoying to deal with for rendering
  // Also any element with aria-label="Map" aria-roledescription="map"
  const selectors = [
    'iframe[src*="google.com/maps"]',
    'iframe[id*="gmap_canvas"]',
    ".maplibregl-map",
    ".mapboxgl-map",
    ".leaflet-container",
    'img[src*="maps.googleapis.com"]',
    '[aria-label="Map"]',
    ".cmp-location-map__map",
    '.map-view[data-role="mapView"]',
    ".google_Map-wrapper",
    ".google_map-wrapper",
    ".googleMap-wrapper",
    ".googlemap-wrapper",
    ".ls-map-canvas",
    ".gmapcluster",
    "#googleMap",
    "#googleMaps",
    "#googlemaps",
    "#googlemap",
    "#google_map",
    "#google_maps",
    "#MapId",
    ".geolocation-map-wrapper",
    ".locatorMap",
  ];

  document.querySelectorAll(selectors.join(", ")).forEach((element) => {
    const currentOpacity = window.getComputedStyle(element).opacity;
    // Store current opacity
    element.setAttribute("data-original-opacity", currentOpacity);

    (element as HTMLElement).style.opacity = "0";
  });
};

const showMapElements = () => {
  const elements = document.querySelectorAll(
    `[${GOOGLE_MAPS_OPACITY_CONTROL}]`,
  );
  elements.forEach((element) => {
    (element as HTMLElement).style.opacity =
      element.getAttribute("data-original-opacity") || "1";
  });
};

window.hideNonTagElements = () => {
  const allElements = getAllElementsInAllFrames();
  allElements.forEach((el) => {
    const element = el as HTMLElement;

    if (element.style.visibility) {
      element.setAttribute(
        reworkdVisibilityAttribute,
        element.style.visibility,
      );
    }

    if (!element.id.startsWith(tarsierId)) {
      element.style.visibility = "hidden";
    } else {
      element.style.visibility = "visible";
    }
  });
};

window.fixNamespaces = (tagName: string): string => {
  // Namespaces in XML give elements unique prefixes (e.g., "a:tag").
  // Standard XPath with namespaces can fail to find elements.
  // The `name()` function returns the full element name, including the prefix.
  // Using "/*[name()='a:tag']" ensures the XPath matches the element correctly.
  const validNamespaceTag = /^[a-zA-Z_][\w\-.]*:[a-zA-Z_][\w\-.]*$/;

  // Split the tagName by '#' (ID) and '.' (class) to isolate the tag name part
  const tagOnly = tagName.split(/[#.]/)[0];

  if (validNamespaceTag.test(tagOnly)) {
    // If it's a valid namespaced tag, wrap with the name() function
    return tagName.replace(tagOnly, `*[name()="${tagOnly}"]`);
  } else {
    return tagName;
  }
};

window.revertVisibilities = () => {
  const allElements = getAllElementsInAllFrames();
  allElements.forEach((el) => {
    const element = el as HTMLElement;
    if (element.getAttribute(reworkdVisibilityAttribute)) {
      element.style.visibility =
        element.getAttribute(reworkdVisibilityAttribute) || "true";
    } else {
      element.style.removeProperty("visibility");
    }
  });
};
