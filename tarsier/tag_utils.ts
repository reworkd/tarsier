// noinspection JSUnusedGlobalSymbols
interface Window {
  tagifyWebpage: (tagLeafTexts?: boolean) => { [key: number]: string };
  removeTags: () => void;
}

const elIsClean = (el: HTMLElement) => {
  if (el.style && el.style.display === "none") return false;
  if (el.hidden) return false;
  // @ts-ignore
  if (el.disabled) return false;

  const rect = el.getBoundingClientRect();
  if (rect.width === 0 || rect.height === 0) return false;

  if (el.tagName === "SCRIPT") return false;
  if (el.tagName === "STYLE") return false;

  return true;
};

const inputs = ["a", "button", "textarea", "select", "details", "label"];
const isInteractable = (el: Element) =>
  inputs.includes(el.tagName.toLowerCase()) ||
  // @ts-ignore
  (el.tagName.toLowerCase() === "input" && el.type !== "hidden") ||
  el.role === "button";

const emptyTagWhitelist = ["input", "textarea", "select", "button"];
const isEmpty = (el: HTMLElement) => {
  const tagName = el.tagName.toLowerCase();
  if (emptyTagWhitelist.includes(tagName)) return false;
  if ("innerText" in el && el.innerText.trim().length === 0) {
    // look for svg or img in the element
    const svg = el.querySelector("svg");
    const img = el.querySelector("img");

    if (svg || img) return false;

    return true;
  }

  return false;
};

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

    let prefix = element.tagName.toLowerCase();
    let sibling_index = 1;

    let sibling = element.previousElementSibling;
    while (sibling) {
      if (sibling.tagName === element.tagName) {
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
      path_parts.unshift(prefix);
      return "//" + path_parts.join("/");
    } else if (element.className) {
      const classList = Array.from(element.classList);
      const class_conditions = classList
        .map(
          (single_class) =>
            `contains(concat(" ", normalize-space(@class), " "), " ${single_class} ")`,
        )
        .join(" and ");

      if (class_conditions.length > 0) {
        prefix += `[${class_conditions}]`;
      }
    }

    path_parts.unshift(prefix);
    // @ts-ignore
    element = element.parentNode;
  }
  return iframe_str + "//" + path_parts.join("/");
}

window.tagifyWebpage = (tagLeafTexts = false) => {
  window.removeTags();

  let idNum = 0;
  let idToXpath: Record<number, string> = {};

  // @ts-ignore
  let allElements: HTMLElement[] = [...document.body.querySelectorAll("*")];
  const iframes = document.getElementsByTagName("iframe");

  // add elements in iframes to allElements
  for (let i = 0; i < iframes.length; i++) {
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

  // ignore all children of interactable elements
  allElements.map((el) => {
    if (isInteractable(el as Element)) {
      el.childNodes.forEach((child) => {
        const index = allElements.indexOf(child as HTMLElement);
        if (index > -1) {
          allElements.splice(index, 1);
        }
      });
    }
  });

  const inputTags = ["input", "textarea", "select"];

  for (let el of allElements) {
    if (isEmpty(el) || !elIsClean(el)) {
      continue;
    }

    const intractable = isInteractable(el);
    const elTagName = el.tagName.toLowerCase();
    const idStr = inputTags.includes(elTagName) ? `{${idNum}} ` : `[${idNum}] `;
    idToXpath[idNum] = getElementXPath(el);

    // create the span for the id tag
    let idSpan = document.createElement("span");
    idSpan.style.all = "inherit";
    idSpan.style.display = "inline";
    idSpan.textContent = idStr;
    idSpan.id = "__tarsier_id";

    if (intractable) {
      if (!inputTags.includes(elTagName)) {
        el.prepend(idSpan);
      } else if (elTagName === "textarea" || elTagName === "input") {
        el.prepend(idSpan);
      } else if (elTagName === "select") {
        // leave select blank - we'll give a tag ID to the options
      }
    } else {
      if (
        tagLeafTexts &&
        /\S/.test(el.textContent || "") &&
        Array.from(el.childNodes).every(
          (node) => node.nodeType === Node.TEXT_NODE,
        )
      ) {
        // This is a leaf element with non-whitespace text
        el.prepend(idSpan);
      }
    }

    idNum++;
  }

  return idToXpath;
};

window.removeTags = () => {
  const tags = document.querySelectorAll("#__tarsier_id");
  tags.forEach((tag) => tag.remove());
};
