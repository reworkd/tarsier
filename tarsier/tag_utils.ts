// noinspection JSUnusedGlobalSymbols
interface ColouredElem {
  id: number;
  idSymbol: string;
  color: string;
  xpath: string;
  midpoint: [number, number];
  normalizedMidpoint: [number, number];
  width: number;
  height: number;
  isFixed: boolean;
  fixedPosition: string; // 'top', 'bottom', 'none'
  boundingBoxX: number;
  boundingBoxY: number;
}
interface Window {
  // Playwright's .evaluate method runs javascript code in an isolated scope.
  // This means that subsequent calls to .evaluate will not have access to the functions defined in this file
  // since they will be in an inaccessible scope. To circumvent this, we attach the following methods to the
  // window which is always available globally when run in a browser environment.
  tagifyWebpage: (tagLeafTexts?: boolean) => { [p: number]: TagMetadata };
  removeTags: () => void;
  hideNonTagElements: () => void;
  revertVisibilities: () => void;
  fixNamespaces: (tagName: string) => string;
  colourBasedTagify: (
    tagLeafTexts?: boolean,
    tagless?: boolean,
  ) => {
    colorMapping: ColouredElem[];
    tagMappingWithTagMeta: { [p: number]: TagMetadata };
    insertedIdStrings: string[];
  };
  hideNonColouredElements: () => void;
  createTextBoundingBoxes: () => void;
  documentDimensions: () => { width: number; height: number };
  getElementBoundingBoxes: (xpath: string) => {
    text: string;
    top: number;
    left: number;
    width: number;
    height: number;
  }[];
  checkHasTaggedChildren: (xpath: string) => boolean;
  setElementVisibilityToHidden: (xpath: string) => void;
  reColourElements: (colouredElems: ColouredElem[]) => ColouredElem[];
  disableTransitionsAndAnimations: () => void;
  enableTransitionsAndAnimations: () => void;
  restoreDOM: (storedDOM: string) => void;
  storeDOM: () => string;
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

let originalDOM = document.body.cloneNode(true);

window.storeDOM = () => {
  originalDOM = document.body.cloneNode(true);
  console.log("DOM state stored.");
  return document.body.outerHTML;
};

window.restoreDOM = (storedDOM) => {
  console.log("Restoring DOM");
  if (storedDOM) {
    document.body.innerHTML = storedDOM;
  } else {
    console.error("No DOM state was provided.");
  }
};

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

      // If the id is unique and we have enough path parts, we can stop
      if (path_parts.length > 3) {
        path_parts.unshift(prefix);
        return "//" + path_parts.join("/");
      }
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
  const tagMetadataDict = insertTags(elementsToTag, tagLeafTexts);
  shrinkCollidingTags();
  ensureMinimumTagFontSizes();

  return tagMetadataDict;
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
    if (isTextInsertable(el)) return "#";
    return el.tagName.toLowerCase() === "a" ? "@" : "$";
  }
  return isImageElement(el) ? "%" : "";
}

function insertTags(
  elementsToTag: HTMLElement[],
  tagLeafTexts: boolean,
): { [p: number]: TagMetadata } {
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
    tarsierId: number;
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
      tarsierId: idNum,
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

  const tagDataDict: { [key: number]: TagMetadata } = {};
  tagDataList.forEach((tagData) => {
    const elementHTML = getOpeningTag(tagData.element);
    const symbol = getTagSymbol(tagData.element) || "";
    const idString = `[ ${symbol}${symbol ? " " : ""}${tagData.tarsierId} ]`;

    const elementText = tagData.originalTextContent;

    tagDataDict[tagData.tarsierId] = {
      tarsierId: tagData.tarsierId,
      elementName: tagData.element.tagName.toLowerCase(),
      openingTagHTML: elementHTML,
      xpath: tagData.xpath,
      elementText: elementText,
      textNodeIndex: tagData.textNodeIndex,
      idSymbol: symbol,
      idString: idString,
    };
  });
  return tagDataDict;
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
  }

  return tagName;
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

function hasDirectTextContent(element: HTMLElement): boolean {
  const childNodesArray = Array.from(element.childNodes);
  for (let node of childNodesArray) {
    if (
      node.nodeType === Node.TEXT_NODE &&
      node.textContent &&
      node.textContent.trim().length > 0
    ) {
      return true;
    }
  }
  return false;
}

window.hideNonColouredElements = () => {
  const allElements = document.body.querySelectorAll("*");
  allElements.forEach((el) => {
    const element = el as HTMLElement;
    if (element.style.visibility) {
      element.setAttribute(
        reworkdVisibilityAttribute,
        element.style.visibility,
      );
    }

    if (
      !element.hasAttribute("data-colored") ||
      element.getAttribute("data-colored") !== "true"
    ) {
      element.style.visibility = "hidden";
    } else {
      element.style.visibility = "visible";
    }
  });
};

function getNextColors(totalTags: number): string[] {
  let colors = [];
  let step = Math.ceil(256 / Math.cbrt(totalTags)); // Start with the initial step size

  while (colors.length < totalTags) {
    colors = []; // Reset the colors array for each iteration
    for (let r = 0; r < 256; r += step) {
      for (let g = 0; g < 256; g += step) {
        for (let b = 0; b < 256; b += step) {
          colors.push(`rgb(${r}, ${g}, ${b})`);
          if (colors.length >= totalTags) {
            // Stop generating colors once we reach the required amount
            break;
          }
        }
        if (colors.length >= totalTags) {
          break;
        }
      }
      if (colors.length >= totalTags) {
        break;
      }
    }

    if (colors.length < totalTags) {
      step--; // Decrease the step to increase the number of generated colors
      if (step <= 0) {
        throw new Error("Step cannot be reduced further.");
      }
    }
  }

  for (let i = colors.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [colors[i], colors[j]] = [colors[j], colors[i]];
  }

  return colors.slice(0, totalTags);
}

function colorDistance(color1: string, color2: string): number {
  const rgb1 = color1.match(/\d+/g)!.map(Number);
  const rgb2 = color2.match(/\d+/g)!.map(Number);
  return Math.sqrt(
    Math.pow(rgb1[0] - rgb2[0], 2) +
      Math.pow(rgb1[1] - rgb2[1], 2) +
      Math.pow(rgb1[2] - rgb2[2], 2),
  );
}

function assignColors(
  elements: HTMLElement[],
  colors: string[],
): Map<HTMLElement, string> {
  const colorAssignments = new Map<HTMLElement, string>();
  const assignedColors = new Set<string>();

  elements.forEach((element) => {
    let bestColor: string | null = null;
    let maxMinDistance = -1;

    colors.forEach((color) => {
      if (assignedColors.has(color)) return;

      let minDistance = Infinity;
      assignedColors.forEach((assignedColor) => {
        const distance = colorDistance(color, assignedColor);
        minDistance = Math.min(minDistance, distance);
      });

      if (minDistance > maxMinDistance) {
        maxMinDistance = minDistance;
        bestColor = color;
      }
    });

    if (bestColor) {
      colorAssignments.set(element, bestColor);
      assignedColors.add(bestColor);
    } else {
      // Fallback: Assign the first unassigned color if no bestColor is found
      const remainingColors = colors.filter((c) => !assignedColors.has(c));
      bestColor = remainingColors[0];
      colorAssignments.set(element, bestColor);
      assignedColors.add(bestColor);
    }
  });

  return colorAssignments;
}

window.colourBasedTagify = (
  tagLeafTexts = false,
  tagless: boolean = false,
): {
  colorMapping: ColouredElem[];
  tagMappingWithTagMeta: { [p: number]: TagMetadata };
  insertedIdStrings: string[];
} => {
  const tagMappingWithTagMeta = window.tagifyWebpage(tagLeafTexts);

  window.removeTags();

  const insertedIdStrings = insertIdStringsIntoTextNodes(
    tagMappingWithTagMeta,
    tagless,
  );

  const elements = collectElementsToColor(tagMappingWithTagMeta);

  const colorAssignments = getColorsForElements(elements);

  const colorMapping = createColorMappingAndApplyStyles(
    elements,
    colorAssignments,
    tagMappingWithTagMeta,
  );

  return { colorMapping, tagMappingWithTagMeta, insertedIdStrings };
};

function insertIdStringsIntoTextNodes(
  tagMappingWithTagMeta: { [key: number]: TagMetadata },
  tagless: boolean,
): string[] {
  let insertedIdStrings: string[] = [];
  Object.entries(tagMappingWithTagMeta).forEach(([id, meta]) => {
    if (meta.textNodeIndex !== undefined && meta.idString !== undefined) {
      const xpathWithTextNode = `${meta.xpath}/text()[${meta.textNodeIndex}]`;
      const textNode = document.evaluate(
        xpathWithTextNode,
        document,
        null,
        XPathResult.FIRST_ORDERED_NODE_TYPE,
        null,
      ).singleNodeValue as Text;

      if (textNode && !tagless) {
        textNode.data = `${meta.idString} ${textNode.data}`;
        insertedIdStrings.push(meta.idString);
      }
    }
  });
  return insertedIdStrings;
}

function collectElementsToColor(tagMappingWithTagMeta: {
  [key: number]: TagMetadata;
}): HTMLElement[] {
  const elements: HTMLElement[] = [];
  const viewportWidth = window.innerWidth;
  Object.values(tagMappingWithTagMeta).forEach((meta) => {
    const { tarsierId: id, xpath } = meta;
    const node = document.evaluate(
      xpath,
      document,
      null,
      XPathResult.FIRST_ORDERED_NODE_TYPE,
      null,
    ).singleNodeValue;

    if (node instanceof HTMLElement) {
      const computedStyle = getComputedStyle(node);
      if (computedStyle.display === "contents") {
        node.style.removeProperty("display");
      }
      const rect = node.getBoundingClientRect();
      if (
        rect.width > 0 &&
        rect.height > 0 &&
        rect.left >= 0 &&
        rect.right <= viewportWidth
      ) {
        node.setAttribute("data-id", id.toString());
        elements.push(node);
      }
    }
  });
  return elements;
}

function getColorsForElements(
  elements: HTMLElement[],
): Map<HTMLElement, string> {
  const totalTags = elements.length;
  const colors = getNextColors(totalTags);
  const colorAssignments = assignColors(elements, colors);
  return colorAssignments;
}

function createColorMappingAndApplyStyles(
  elements: HTMLElement[],
  colorAssignments: Map<HTMLElement, string>,
  tagMappingWithTagMeta: { [key: number]: TagMetadata },
): ColouredElem[] {
  const colorMapping: ColouredElem[] = [];
  const bodyRect = document.body.getBoundingClientRect();
  const attribute = "data-colored";
  const taggedElements = new Set(
    Object.values(tagMappingWithTagMeta).map((meta) => meta.xpath),
  );

  elements.forEach((element) => {
    const id = parseInt(element.getAttribute("data-id")!);
    const color = colorAssignments.get(element)!;
    const rect = element.getBoundingClientRect();
    const midpoint: [number, number] = [rect.left, rect.top];
    const normalizedMidpoint: [number, number] = [
      (midpoint[0] - bodyRect.left) / bodyRect.width,
      (midpoint[1] - bodyRect.top) / bodyRect.height,
    ];

    const symbol = getTagSymbol(element) || "";
    const idSymbol = `[ ${symbol}${symbol ? " " : ""}${id} ]`;

    const { isFixed, fixedPosition } = getFixedPosition(element);

    colorMapping.push({
      id,
      idSymbol,
      color,
      xpath: tagMappingWithTagMeta[id].xpath,
      midpoint,
      normalizedMidpoint,
      width: rect.width,
      height: rect.height,
      isFixed,
      fixedPosition,
      boundingBoxX: rect.x,
      boundingBoxY: rect.y,
    });

    applyStylesToElement(element, color, attribute, taggedElements, rect);
  });
  return colorMapping;
}

function applyStylesToElement(
  element: HTMLElement,
  color: string,
  attribute: string,
  taggedElements: Set<string>,
  rect: DOMRect,
) {
  if (
    element.tagName.toLowerCase() === "input" &&
    (element as HTMLInputElement).type === "checkbox"
  ) {
    applyStylesToCheckbox(element as HTMLInputElement, color, attribute);
  } else if (element.tagName.toLowerCase() === "img") {
    applyStylesToImage(element as HTMLImageElement, color, attribute);
  } else {
    element.style.setProperty("background-color", color, "important");
    element.style.setProperty("color", color, "important");
    element.style.setProperty("border-color", color, "important");
    element.style.setProperty("opacity", "1", "important");
    element.setAttribute(attribute, "true");
  }

  if (element.tagName.toLowerCase() === "a") {
    applyStylesToLink(element, taggedElements, rect);
  }

  // Hide untagged child elements
  Array.from(element.children).forEach((child) => {
    const childXpath = getElementXPath(child as HTMLElement);
    const childComputedStyle = window.getComputedStyle(child);
    if (
      !taggedElements.has(childXpath) &&
      childComputedStyle.display !== "none"
    ) {
      (child as HTMLElement).style.visibility = "hidden";
    }
  });
}

function applyStylesToCheckbox(
  checkboxElement: HTMLInputElement,
  color: string,
  attribute: string,
) {
  const originalWidth = checkboxElement.offsetWidth + 2 + "px";
  const originalHeight = checkboxElement.offsetHeight + 2 + "px";

  // Apply styles to make the checkbox appear filled
  checkboxElement.style.setProperty("width", originalWidth, "important");
  checkboxElement.style.setProperty("height", originalHeight, "important");
  checkboxElement.style.setProperty("background-color", color, "important");
  checkboxElement.style.setProperty(
    "border",
    `2px solid ${color}`,
    "important",
  );
  checkboxElement.style.setProperty("appearance", "none", "important");
  checkboxElement.style.setProperty("border-radius", "4px", "important");
  checkboxElement.style.setProperty("position", "relative", "important");
  checkboxElement.style.setProperty("cursor", "pointer", "important");
  checkboxElement.setAttribute(attribute, "true");

  // Add event listener for checkbox state change
  checkboxElement.addEventListener("change", function () {
    if (checkboxElement.checked) {
      checkboxElement.style.setProperty("background-color", color, "important");
    } else {
      checkboxElement.style.setProperty("background-color", color, "important");
    }
  });
}

function applyStylesToImage(
  element: HTMLImageElement,
  color: string,
  attribute: string,
) {
  const imageWidth = element.offsetWidth;
  const imageHeight = element.offsetHeight;

  const rgbToHex = (rgb: string) => {
    const result = rgb.match(/\d+/g);
    return result
      ? result.map((x) => parseInt(x).toString(16).padStart(2, "0")).join("")
      : "000000";
  };

  const hexColor = rgbToHex(color);
  const newSrc = `https://craftypixels.com/placeholder-image/${imageWidth}x${imageHeight}/${hexColor}/${hexColor}`;

  element.setAttribute("src", newSrc);
  element.setAttribute(attribute, "true");
}

function applyStylesToLink(
  element: HTMLElement,
  taggedElements: Set<string>,
  rect: DOMRect,
) {
  const computedStyle = window.getComputedStyle(element);
  if (computedStyle.backgroundImage !== "none") {
    element.style.backgroundImage = "none";
  }

  let hasTextChild = false;
  let hasImageChild = false;
  let boundingBoxGreaterThanZero = rect.width > 0 && rect.height > 0;
  let hasUnTaggedTextElement = false;

  // Check for text nodes and images within child elements
  Array.from(element.children).forEach((child) => {
    const childElement = child as HTMLElement;
    if (
      childElement.textContent &&
      childElement.textContent.trim().length > 0
    ) {
      hasTextChild = true;
    }
    if (childElement.tagName.toLowerCase() === "img") {
      hasImageChild = true;
    }
    // Check if child element itself is not tagged
    const childXpath = getElementXPath(childElement);
    if (
      !taggedElements.has(childXpath) &&
      childElement.textContent &&
      childElement.textContent.trim().length > 0
    ) {
      hasUnTaggedTextElement = true;
    }
  });

  if (
    (!hasTextChild &&
      !hasImageChild &&
      !hasDirectTextContent(element) &&
      !boundingBoxGreaterThanZero) ||
    hasUnTaggedTextElement
  ) {
    element.style.width = `${rect.width}px`;
    element.style.height = `${rect.height}px`;
    element.style.display = "block";
  }
}

function createIdSymbol(idNum: number, el: HTMLElement): string {
  let idStr: string;
  if (isInteractable(el)) {
    if (isTextInsertable(el)) idStr = `[ # ${idNum} ]`;
    else if (el.tagName.toLowerCase() == "a") idStr = `[ @ ${idNum} ]`;
    else idStr = `[ $ ${idNum} ]`;
  } else {
    idStr = `[ ${idNum} ]`;
  }
  return idStr;
}

window.createTextBoundingBoxes = () => {
  const style = document.createElement("style");
  document.head.appendChild(style);
  if (style.sheet) {
    style.sheet.insertRule(
      `
        .tarsier-highlighted-word, .tarsier-space {
          border: 0px solid orange;
          display: inline-block !important;
          visibility: visible;
        }
      `,
      0,
    );
  }

  function applyHighlighting(root: Document | HTMLElement) {
    root.querySelectorAll("body *").forEach((element) => {
      if (
        ["SCRIPT", "STYLE", "IFRAME", "INPUT", "TEXTAREA"].includes(
          element.tagName,
        )
      ) {
        return;
      }
      let childNodes = Array.from(element.childNodes);
      childNodes.forEach((node) => {
        if (
          node.nodeType === 3 &&
          node.textContent &&
          node.textContent.trim().length > 0
        ) {
          let textContent = node.textContent.replace(/\u00A0/g, " ");

          const tarsierTagRegex = /\[\s*(?:[$@#]?\s*\d+)\s*\]/g;

          if (element.hasAttribute("selected")) {
            let span = document.createElement("span");
            span.className = "tarsier-highlighted-word";
            span.textContent = textContent;
            if (node.parentNode) {
              node.parentNode.replaceChild(span, node);
            }
          } else {
            let parts = textContent.split(tarsierTagRegex);
            let matches = textContent.match(tarsierTagRegex);
            let fragment = document.createDocumentFragment();

            parts.forEach((part, index) => {
              let tokens = part.split(/(\s+)/g);
              tokens.forEach((token) => {
                let span = document.createElement("span");
                if (token.trim().length === 0) {
                  span.className = "tarsier-space";
                } else {
                  span.className = "tarsier-highlighted-word";
                }
                span.textContent = token;
                fragment.appendChild(span);
              });

              if (matches && matches[index]) {
                let span = document.createElement("span");
                span.className = "tarsier-highlighted-word";
                span.textContent = matches[index];
                fragment.appendChild(span);
              }
            });

            if (fragment.childNodes.length > 0 && node.parentNode) {
              element.insertBefore(fragment, node);
              node.remove();
            }
          }
        }
      });
    });
  }

  applyHighlighting(document);

  document.querySelectorAll("iframe").forEach((iframe) => {
    try {
      iframe.contentWindow?.postMessage({ action: "highlight" }, "*");
    } catch (error) {
      console.error("Error accessing iframe content: ", error);
    }
  });
};

window.documentDimensions = () => {
  return {
    width: document.documentElement.scrollWidth,
    height: document.documentElement.scrollHeight,
  };
};

window.getElementBoundingBoxes = (xpath: string) => {
  const element = document.evaluate(
    xpath,
    document,
    null,
    XPathResult.FIRST_ORDERED_NODE_TYPE,
    null,
  ).singleNodeValue as HTMLElement;
  if (element) {
    const isValidText = (text: string) => text && text.trim().length > 0;
    let dropDownElem = element.querySelector("option[selected]");

    if (!dropDownElem) {
      dropDownElem = element.querySelector("option");
    }

    if (dropDownElem) {
      const elemText = dropDownElem.textContent || "";
      if (isValidText(elemText)) {
        const parentRect = element.getBoundingClientRect();
        return [
          {
            text: elemText.trim(),
            top: parentRect.top + window.scrollY,
            left: parentRect.left + window.scrollX,
            width: parentRect.width,
            height: parentRect.height,
          },
        ];
      } else {
        return [];
      }
    }
    let placeholderText = " ";
    if (
      (element.tagName.toLowerCase() === "input" ||
        element.tagName.toLowerCase() === "textarea") &&
      (element as HTMLInputElement).placeholder
    ) {
      placeholderText = (element as HTMLInputElement).placeholder;
    } else if (element.tagName.toLowerCase() === "a") {
      placeholderText = " ";
    } else if (element.tagName.toLowerCase() === "img") {
      placeholderText = (element as HTMLImageElement).alt || " ";
    }

    const words = element.querySelectorAll(
      ":scope > .tarsier-highlighted-word",
    ) as NodeListOf<HTMLElement>;
    const boundingBoxes = Array.from(words)
      .map((word) => {
        const rect = (word as HTMLElement).getBoundingClientRect();
        return {
          text: word.innerText || "",
          top: rect.top + window.scrollY,
          left: rect.left + window.scrollX,
          width: rect.width,
          height: rect.height * 0.75,
        };
      })
      .filter(
        (box) =>
          box.width > 0 &&
          box.height > 0 &&
          box.top >= 0 &&
          box.left >= 0 &&
          isValidText(box.text),
      );

    if (words.length === 0) {
      const elementRect = element.getBoundingClientRect();
      return [
        {
          text: placeholderText,
          top: elementRect.top + window.scrollY,
          left: elementRect.left + window.scrollX,
          width: elementRect.width,
          height: elementRect.height * 0.75,
        },
      ];
    }

    return boundingBoxes;
  } else {
    return [];
  }
};

function getFixedPosition(element: HTMLElement): {
  isFixed: boolean;
  fixedPosition: string;
} {
  let isFixed = false;
  let fixedPosition = "none";
  let currentElement: HTMLElement | null = element;

  while (currentElement) {
    const style = window.getComputedStyle(currentElement);
    if (style.position === "fixed") {
      isFixed = true;
      const rect = currentElement.getBoundingClientRect();
      if (rect.top === 0) {
        fixedPosition = "top";
      } else if (rect.bottom === window.innerHeight) {
        fixedPosition = "bottom";
      }
      break;
    }
    currentElement = currentElement.parentElement;
  }

  return { isFixed, fixedPosition };
}

window.checkHasTaggedChildren = (xpath: string): boolean => {
  const element = document.evaluate(
    xpath,
    document,
    null,
    XPathResult.FIRST_ORDERED_NODE_TYPE,
    null,
  ).singleNodeValue as HTMLElement | null;
  if (element) {
    const taggedChildren = element.querySelector('[data-colored="true"]');
    return !!taggedChildren;
  }
  return false;
};

window.setElementVisibilityToHidden = (xpath: string) => {
  const element = document.evaluate(
    xpath,
    document,
    null,
    XPathResult.FIRST_ORDERED_NODE_TYPE,
    null,
  ).singleNodeValue as HTMLElement | null;
  if (element) {
    element.style.visibility = "hidden";
  } else {
    console.error(
      `Tried to hide element. Element not found for XPath: ${xpath}`,
    );
  }
};

window.reColourElements = (colouredElems: ColouredElem[]): ColouredElem[] => {
  const totalTags = colouredElems.length;
  const colors = getNextColors(totalTags);

  const elements: HTMLElement[] = colouredElems.map((elem) => {
    const element = document.evaluate(
      elem.xpath,
      document,
      null,
      XPathResult.FIRST_ORDERED_NODE_TYPE,
      null,
    ).singleNodeValue as HTMLElement;
    element.setAttribute("data-id", elem.id.toString());
    return element;
  });

  const colorAssignments = assignColors(elements, colors);

  const bodyRect = document.body.getBoundingClientRect();

  const updatedColouredElems = colouredElems.map((elem) => {
    const element = document.evaluate(
      elem.xpath,
      document,
      null,
      XPathResult.FIRST_ORDERED_NODE_TYPE,
      null,
    ).singleNodeValue as HTMLElement;
    const color = colorAssignments.get(element)!;
    const rect = element.getBoundingClientRect();
    const midpoint: [number, number] = [rect.left, rect.top];
    const normalizedMidpoint: [number, number] = [
      (midpoint[0] - bodyRect.left) / bodyRect.width,
      (midpoint[1] - bodyRect.top) / bodyRect.height,
    ];

    element.style.setProperty("background-color", color, "important");
    element.style.setProperty("color", color, "important");
    element.style.setProperty("border-color", color, "important");
    element.style.setProperty("opacity", "1", "important");
    element.setAttribute("data-colored", "true");

    return {
      ...elem,
      color,
      midpoint,
      normalizedMidpoint,
      width: rect.width,
      height: rect.height,
      boundingBoxX: rect.x,
      boundingBoxY: rect.y,
    };
  });

  return updatedColouredElems;
};

window.disableTransitionsAndAnimations = () => {
  const style = document.createElement("style");
  style.innerHTML = `
    *, *::before, *::after {
      transition-property: none !important;
      transition-duration: 0s !important;
      transition-timing-function: none !important;
      transition-delay: 0s !important;
      animation: none !important;
      animation-name: none !important;
      animation-duration: 0s !important;
      animation-timing-function: none !important;
      animation-delay: 0s !important;
      animation-iteration-count: 1 !important;
      animation-direction: normal !important;
      animation-fill-mode: none !important;
      animation-play-state: paused !important;
    }
  `;
  style.id = "disable-transitions";
  document.head.appendChild(style);
};

window.enableTransitionsAndAnimations = () => {
  const style = document.getElementById("disable-transitions");
  if (style) {
    style.remove();
  }
};

// LEAVE AS LAST LINE. DO NOT REMOVE
// JavaScript scripts, when run in the JavaScript console, will evaluate to the last line/expression in the script
// This tag utils file will typically end in a function assignment
// Function assignments will evaluate to the created function
// If playwright .evaluate(JS_CODE) evaluates to a function, IT WILL CALL THE FUNCTION
// This means that the last function in this file will randomly get called whenever we load in the JS,
// unless we have something like this console.log (Which returns undefined) is placed at the end

console.log("Tarsier tag utils loaded");
