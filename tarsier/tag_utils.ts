// noinspection JSUnusedGlobalSymbols
interface Window {
  tagifyWebpage: (tagLeafTexts?: boolean) => { [key: number]: string };
  removeTags: () => void;
}

const tarsierId = "__tarsier_id";
const tarsierSelector = `#${tarsierId}`;

const elIsClean = (el: HTMLElement) => {
  const rect = el.getBoundingClientRect();
  const computedStyle = window.getComputedStyle(el);

  // @ts-ignore
  const isHidden = computedStyle.visibility === 'hidden' || computedStyle.display === 'none' || el.hidden || el.disabled;
  const isTransparent = computedStyle.opacity === '0';
  const isZeroSize = rect.width === 0 || rect.height === 0;
  const isScriptOrStyle = el.tagName === "SCRIPT" || el.tagName === "STYLE";
  return !isHidden && !isTransparent && !isZeroSize && !isScriptOrStyle;
};

const inputs = ["a", "button", "textarea", "select", "details", "label"];
const isInteractable = (el: HTMLElement) => {
  return inputs.includes(el.tagName.toLowerCase()) ||
    // @ts-ignore
    (el.tagName.toLowerCase() === "input" && el.type !== "hidden") ||
    el.role === "button"
}

const text_input_types = ["text", "password", "email", "search", "url", "tel", "number"];
const isTextInsertable = (el: HTMLElement) =>
  el.tagName.toLowerCase() === "textarea" ||
  ((el.tagName.toLowerCase() === "input" &&
    text_input_types.includes((el as HTMLInputElement).type)));

const emptyTagWhitelist = ["input", "textarea", "select", "button"];
const isEmpty = (el: HTMLElement) => {
  const tagName = el.tagName.toLowerCase();
  if (emptyTagWhitelist.includes(tagName)) return false;
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
  return (
    rect.top >= 0 &&
    rect.left >= 0 &&
    rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
    rect.right <= (window.innerWidth || document.documentElement.clientWidth)
  );
}

function getElementXPath(element: HTMLElement | null) {
  let path_parts = [];

  let iframe_str = "";
  if (element && element.ownerDocument !== window.document) {
    // assert element.iframe_index !== undefined, "Element is not in the main document and does not have an iframe_index attribute";
    iframe_str = `iframe[${element.getAttribute("iframe_index")}]`;
  }

  while(element) {
    if (!element.tagName) {
      element = element.parentNode as HTMLElement | null;
      continue;
    }

    let prefix = element.tagName.toLowerCase();
    let sibling_index = 1;

    let sibling = element.previousElementSibling;
    while(sibling) {
      if (sibling.tagName === element.tagName) {
        sibling_index++;
      }
      sibling = sibling.previousElementSibling;
    }

    // Check next siblings to determine if index should be added
    let nextSibling = element.nextElementSibling;
    let shouldAddIndex = false;
    while(nextSibling) {
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
      const classList = Array.from(element.classList);
      prefix += `[@class="${element.className}"]`;
    }

    path_parts.unshift(prefix);
    element = element.parentNode as HTMLElement | null;
  }
  return iframe_str + "//" + path_parts.join("/");
}

function create_tagged_span(idNum: number, el: HTMLElement) {
  let idStr: string;
  if (isInteractable(el)) {
    if (isTextInsertable(el))
      idStr = `[#${idNum}]`;
    else if (el.tagName.toLowerCase() == 'a')
      idStr = `[@${idNum}]`;
    else
      idStr = `[$${idNum}]`;
  } else {
    idStr = `[${idNum}]`;
  }

  let idSpan = document.createElement("span");
  idSpan.id = tarsierId;
  idSpan.style.position = "relative";
  idSpan.style.display = "inline";
  idSpan.style.color = "white";
  idSpan.style.backgroundColor = "red";
  idSpan.style.padding = "1.5px";
  idSpan.style.borderRadius = "3px";
  idSpan.style.fontWeight = "bold";
  // idSpan.style.fontSize = "15px"; // Removing because OCR won't see text among large font
  idSpan.style.fontFamily = "Arial";
  idSpan.style.margin = "1px";
  idSpan.style.lineHeight = "1.25";
  idSpan.style.letterSpacing = "2px";
  idSpan.style.zIndex = '2140000046';
  idSpan.style.clip = 'auto';
  idSpan.style.height = 'fit-content';
  idSpan.style.width = 'fit-content';
  idSpan.style.minHeight = 'fit-content';
  idSpan.style.minWidth = 'fit-content';
  idSpan.style.maxHeight = 'unset';
  idSpan.style.maxWidth = 'unset';
  idSpan.textContent = idStr;
  idSpan.style.webkitTextFillColor = 'white';
  idSpan.style.textShadow = '';
  idSpan.style.textDecoration = 'none';
  idSpan.style.letterSpacing = '0px';
  return idSpan;
}

window.tagifyWebpage = (tagLeafTexts = false) => {
  window.removeTags();
  hideMapElements();

  let idNum = 0;
  let idToXpath: Record<number, string> = {};

  // @ts-ignore
  let allElements: HTMLElement[] = [...document.body.querySelectorAll("*")];
  const iframes = document.getElementsByTagName("iframe");

  // add elements in iframes to allElements
  for(let i = 0; i < iframes.length; i++) {
    try {
      const frame = iframes[i];
      console.log("iframe!", iframes[i]);
      const iframeDocument =
        frame.contentDocument || frame.contentWindow?.document;

      // @ts-ignore
      const iframeElements = [...iframeDocument.querySelectorAll("*")];
      iframeElements.forEach((el) => el.setAttribute("iframe_index", i));
      allElements.push(...iframeElements);
    } catch (e) {
      // Cross-origin iframe error
      console.error("Cross-origin iframe:", e);
    }
  }

  // ignore all descendants of interactable elements
  allElements.map((el) => {
    if (isInteractable(el)) {
      // Remove all direct children
      el.childNodes.forEach((child) => {
        const index = allElements.indexOf(child as HTMLElement);
        if (index > -1) {
          allElements.splice(index, 1);
        }
      });

      // Remove all interactable sub children
      el.querySelectorAll("*").forEach((child) => {
        const index = allElements.indexOf(child as HTMLElement);
        if (index > -1 && isInteractable(child as HTMLElement)) {
          allElements.splice(index, 1);
        }
      });
    }
  });

  for(let el of allElements) {
    if (isEmpty(el) || !elIsClean(el)) {
      continue;
    }


    if (isInteractable(el)) {
      idToXpath[idNum] = getElementXPath(el);
      idNum++;
    } else if (tagLeafTexts) {
      for(let child of Array.from(el.childNodes)) {
        if (child.nodeType === Node.TEXT_NODE && /\S/.test(child.textContent || "")) {
          // This is a text node with non-whitespace text
          idToXpath[idNum] = getElementXPath(el);
          idNum++;
        }
      }
    }
  }

  idNum = 0;
  for(let el of allElements) {
    if (isEmpty(el) || !elIsClean(el)) {
      continue;
    }

    let idSpan = create_tagged_span(idNum, el);

    if (isInteractable(el)) {
      if (isTextInsertable(el) && el.parentElement) {
        el.parentElement.insertBefore(idSpan, el);
      } else {
        el.prepend(idSpan);
      }
      idNum++;
    } else if (tagLeafTexts) {
      for(let child of Array.from(el.childNodes)) {
        if (child.nodeType === Node.TEXT_NODE && /\S/.test(child.textContent || "")) {
          // This is a text node with non-whitespace text
          let idSpan = create_tagged_span(idNum, el);
          el.insertBefore(idSpan, child);
          idNum++;
        }
      }
    }
  }

  absolutelyPositionMissingTags();
  return idToXpath;
};

function absolutelyPositionMissingTags() {
  /*
  Some tags don't get displayed on the page properly
  This occurs if the parent element children are disjointed from the parent
  In this case, we absolutely position the tag to the parent element
  */
  const distanceThreshold = 500;

  const tags: NodeListOf<HTMLElement> = document.querySelectorAll(tarsierSelector);
  tags.forEach((tag) => {
    const parent = tag.parentElement as HTMLElement;
    const parentRect = parent.getBoundingClientRect();
    let tagRect = tag.getBoundingClientRect();

    const parentCenter = {
      x: (parentRect.left + parentRect.right) / 2,
      y: (parentRect.top + parentRect.bottom) / 2,
    };

    const tagCenter = {
      x: (tagRect.left + tagRect.right) / 2,
      y: (tagRect.top + tagRect.bottom) / 2,
    };

    const dx = Math.abs(parentCenter.x - tagCenter.x);
    const dy = Math.abs(parentCenter.y - tagCenter.y);
    if (dx > distanceThreshold || dy > distanceThreshold || !elIsClean(tag)) {
      tag.style.position = "absolute";

      // Ensure the tag is positioned within the screen bounds
      let leftPosition = Math.max(0, parentRect.left - (tagRect.right + 3 - tagRect.left));
      leftPosition = Math.min(leftPosition, window.innerWidth - (tagRect.right - tagRect.left));
      let topPosition = Math.max(0, parentRect.top + 3); // Add some top buffer to center align better
      topPosition = Math.min(topPosition, Math.max(window.innerHeight, document.documentElement.scrollHeight) - (tagRect.bottom - tagRect.top));

      tag.style.left = `${leftPosition}px`;
      tag.style.top = `${topPosition}px`;

      parent.removeChild(tag);
      document.body.appendChild(tag);
    }

    tags.forEach((otherTag) => {
      if (tag === otherTag) return;
      let otherTagRect = otherTag.getBoundingClientRect();

      // reduce font of this tag and other tag until they don't overlap
      let fontSize = parseFloat(window.getComputedStyle(tag).fontSize.split("px")[0]);
      let otherFontSize = parseFloat(window.getComputedStyle(otherTag).fontSize.split("px")[0]);

      while (
        (tagRect.left < otherTagRect.right &&
          tagRect.right > otherTagRect.left) &&
        (tagRect.top < otherTagRect.bottom &&
          tagRect.bottom > otherTagRect.top) &&
        fontSize > 0.5 && otherFontSize > 0.5
      ) {
        fontSize -= 0.5;
        otherFontSize -= 0.5;
        tag.style.fontSize = `${fontSize}px`;
        otherTag.style.fontSize = `${otherFontSize}px`;

        tagRect = tag.getBoundingClientRect();
        otherTagRect = otherTag.getBoundingClientRect();
      }
    });
  });
}

window.removeTags = () => {
  const tags = document.querySelectorAll(tarsierSelector);
  tags.forEach((tag) => tag.remove());
  showMapElements();
};

const GOOGLE_MAPS_OPACITY_CONTROL = '__reworkd_google_maps_opacity';

const hideMapElements = (): void => {
  // Also any element with aria-label="Map" aria-roledescription="map"
  const selectors = [
    'iframe[src*="google.com/maps"]',
    'iframe[id*="gmap_canvas"]',
    '.maplibregl-map',
    '.mapboxgl-map',
    '.leaflet-container',
    'img[src*="maps.googleapis.com"]',
    '[aria-label="Map"]',
    '.cmp-location-map__map',
    '.map-view[data-role="mapView"]',
    '.google_Map-wrapper',
    '.google_map-wrapper',
    '.googleMap-wrapper',
    '.googlemap-wrapper',
    '.ls-map-canvas',
    '.gmapcluster',
    '#googleMap',
    '#googleMaps',
    '#googlemaps',
    '#googlemap',
    '#google_map',
    '#google_maps',
    '#MapId',
    '.geolocation-map-wrapper',
    '.locatorMap',
  ];

  document.querySelectorAll(selectors.join(', ')).forEach(element => {
    const currentOpacity = window.getComputedStyle(element).opacity;
    // Store current opacity
    element.setAttribute('data-original-opacity', currentOpacity);

    (element as HTMLElement).style.opacity = '0';
  });
}

const showMapElements = () => {
  const elements = document.querySelectorAll(`[${GOOGLE_MAPS_OPACITY_CONTROL}]`);
  elements.forEach(element => {
    (element as HTMLElement).style.opacity = element.getAttribute('data-original-opacity') || '1';
  });
}
