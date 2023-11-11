// TODO: clean up this file

const elIsClean = (el) => {
    if (el.style && el.style.display === 'none') return false
    if (el.hidden) return false
    if (el.disabled) return false

    const rect = el.getBoundingClientRect()
    if (rect.width === 0 || rect.height === 0) return false

    if (el.tagName === 'SCRIPT') return false
    if (el.tagName === 'STYLE') return false

    return true;
}

const inputs = ['a', 'button', 'textarea', 'select', 'details', 'label']
const isInteractable = (el) => inputs.includes(el.tagName.toLowerCase()) ||
    (el.tagName.toLowerCase() === 'input' && el.type !== 'hidden') ||
    el.role === 'button'

const emptyTagWhitelist = ["input", "textarea", "select", "button"]
const isEmpty = (el) => {
    const tagName = el.tagName.toLowerCase()
    if (emptyTagWhitelist.includes(tagName)) return false
    if ("innerText" in el && el.innerText.trim().length === 0) {
        // look for svg or img in the element
        const svg = el.querySelector("svg")
        const img = el.querySelector("img")

        if (svg || img) return false

        return true
    }

    return false
}

function getElementXPath(element) {
    let path_parts = [];

    let iframe_str = '';
    if (element && element.ownerDocument !== window.document) {
        // assert element.iframe_index !== undefined, "Element is not in the main document and does not have an iframe_index attribute";
        iframe_str = `iframe[${element.getAttribute('iframe_index')}]`
    }

    while (element) {
        if (!element.tagName) {
            element = element.parentNode;
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
            return "//" + path_parts.join('/');
        } else if (element.className) {
            const classList = Array.from(element.classList);
            const class_conditions = classList.map(single_class =>
                `contains(concat(" ", normalize-space(@class), " "), " ${single_class} ")`
            ).join(' and ');

            if (class_conditions.length > 0) {
                prefix += `[${class_conditions}]`;
            }
        }

        path_parts.unshift(prefix);
        element = element.parentNode;
    }
    return iframe_str + "//" + path_parts.join('/');
}



window.tagifyWebpage = (gtCls, gtId) => {
    let numTagsSoFar = 0;
    let gtTagId = null;
    let idToTag = {};

    const allElements = [...document.body.querySelectorAll("*")];
    const iframes = document.getElementsByTagName('iframe');

    for (let i = 0; i < iframes.length; i++) {
        try {
            console.log('iframe!', iframes[i]);
            const iframeDocument = iframes[i].contentDocument || iframes[i].contentWindow.document;
            const iframeElements = [...iframeDocument.querySelectorAll("*")];
            iframeElements.forEach(el => el.setAttribute('iframe_index', i));
            allElements.push(...iframeElements);
        } catch (e) {
            // Cross-origin iframe error
            console.error('Cross-origin iframe:', e);
        }
    }

    for (let el of allElements) {
        const stringifiedClasses = el.classList.toString();
        const isGt = (gtCls === null || stringifiedClasses === gtCls) && (gtId === null || el.id === gtId);

        const empty = isEmpty(el);
        const dirty = !elIsClean(el);
        const uninteractable = !isInteractable(el);

        if (logElements.includes(el)) {
            console.log(`Logging ${el.innerText}, ${empty},${dirty},${uninteractable}`)
        }
        if (empty || dirty || uninteractable) {
            // assert(!isGt, `GT element is marked as unclean or uninteractable. empty=${empty}, dirty=${dirty}, uninteractable=${uninteractable}`)
            continue
        }

        if (isGt) {
            console.log("Tagging GT!", el);
            // assert(gtTagId === null, "Multiple GTs found!")
            gtTagId = numTagsSoFar;
        }

        const specialTags = ["input", "textarea", "select"];

        const tagLower = el.tagName.toLowerCase();
        const tagStr = specialTags.includes(tagLower) ? `{${numTagsSoFar}} ` : `[${numTagsSoFar}] `;
        idToTag[numTagsSoFar] = getElementXPath(el);

        // check if already tagged and remove previous tag if so
        const tagRegex = /[\[\]{]\d+[\[\]}]\s/;
        if (tagRegex.test(el.textContent)) {
            el.textContent = el.textContent.replace(tagRegex, '');
        }
        else if (el.placeholder && tagRegex.test(el.placeholder)) {
            el.placeholder = el.placeholder.replace(tagRegex, '');
        }
        else if (el.value && tagRegex.test(el.value)) {
            el.value = el.value.replace(tagRegex, '');
        }

        if (!specialTags.includes(tagLower)) {
            el.prepend(new Text(tagStr));
            // el.innerText = tagStr + el.innerText
        }
        else if (tagLower === "textarea" || tagLower === "input") {
            if (el.value.length === 0)
                el.placeholder = tagStr + el.placeholder
            else el.value = tagStr + el.value
        }
        else if (tagLower === "select") {
            // leave select blank - we'll give a tag ID to the options
        }

        numTagsSoFar++;
    }

    return [gtTagId, idToTag];
}
logElements = []; // some elements where you can check your classification performance. useful for debugging.
