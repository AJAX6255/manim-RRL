import os
import json
import sys
from playwright.sync_api import sync_playwright

def run_debug():
    url = os.environ.get("TEST_URL", "http://127.0.0.1:8000/")
    print(f"Connecting to live DOM at {url}...")
    
    with sync_playwright() as p:
        browser = None
        # Robust browser selection due to potential disk space limitations
        for channel in ["chrome", "msedge", None]:
            try:
                if channel:
                    browser = p.chromium.launch(headless=True, channel=channel)
                else:
                    browser = p.chromium.launch(headless=True)
                print(f"Launched Chromium with channel={channel}")
                break
            except Exception as e:
                print(f"Skipping channel={channel} due to: {e}")
        
        if not browser:
            print("ERROR: Could not launch any browser. Please check if Chrome/Edge is installed.")
            sys.exit(1)
            
        page = browser.new_page()
        try:
            page.goto(url, wait_until="networkidle")
        except Exception as e:
            print(f"Failed to navigate to {url}: {e}")
            browser.close()
            sys.exit(1)
            
        # JS script to execute in browser context.
        # This script walks the DOM, determines stacking contexts, and gathers elements.
        js_code = """
        () => {
            // HUNTING FOR: Selector naming accuracy to build precise altitude map
            function getUniqueSelector(el) {
                if (el.id) return '#' + el.id;
                if (el === document.body) return 'body';
                if (el === document.documentElement) return 'html';
                
                let path = [];
                let curr = el;
                while (curr && curr.nodeType === Node.ELEMENT_NODE) {
                    let selector = curr.nodeName.toLowerCase();
                    if (curr.id) {
                        selector += '#' + curr.id;
                        path.unshift(selector);
                        break;
                    } else {
                        let sibling = curr;
                        let nth = 1;
                        while (sibling = sibling.previousElementSibling) {
                            if (sibling.nodeName.toLowerCase() === curr.nodeName.toLowerCase()) {
                                nth++;
                            }
                        }
                        if (nth > 1) {
                            selector += `:nth-of-type(${nth})`;
                        }
                    }
                    path.unshift(selector);
                    curr = curr.parentElement;
                }
                return path.join(' > ');
            }

            // HUNTING FOR: Element stacking context creators (W3C specification)
            // Stacking contexts isolate children stacking and can cause z-index isolation.
            function createsStackingContext(el) {
                if (el === document.documentElement) return true;
                const style = window.getComputedStyle(el);
                
                // Positioned and z-index is not 'auto'
                const position = style.position;
                const zIndex = style.zIndex;
                if (position !== 'static' && zIndex !== 'auto') return true;
                
                // Positioned as fixed or sticky
                if (position === 'fixed' || position === 'sticky') return true;
                
                // Child of a flex/grid container with z-index not 'auto'
                const parent = el.parentElement;
                if (parent) {
                    const parentStyle = window.getComputedStyle(parent);
                    if ((parentStyle.display.includes('flex') || parentStyle.display.includes('grid')) && zIndex !== 'auto') {
                        return true;
                    }
                }
                
                // Opacity < 1
                if (parseFloat(style.opacity) < 1) return true;
                
                // Transform, filter, backdrop-filter, etc.
                if (style.transform !== 'none') return true;
                if (style.filter && style.filter !== 'none') return true;
                if (style.backdropFilter && style.backdropFilter !== 'none') return true;
                if (style.perspective && style.perspective !== 'none') return true;
                if (style.mixBlendMode && style.mixBlendMode !== 'normal') return true;
                
                return false;
            }

            const elements = [];
            let domIndex = 0;
            
            // HUNTING FOR: Layout elements and checking backdrop elements (stars/twinkling)
            function walk(el) {
                if (!el || el.nodeType !== Node.ELEMENT_NODE) return;
                
                const style = window.getComputedStyle(el);
                
                // Only consider elements that are visible/displayed in layout
                if (style.display === 'none') {
                    return; // Children of display:none elements are also not rendered
                }
                
                // Gather stacking context path: represents the exact altitude nesting hierarchy
                const stackingPath = [];
                let curr = el;
                while (curr) {
                    if (createsStackingContext(curr)) {
                        const cStyle = window.getComputedStyle(curr);
                        let z = cStyle.zIndex;
                        z = (z === 'auto') ? 0 : parseInt(z, 10);
                        stackingPath.unshift(z);
                    }
                    curr = curr.parentElement;
                }
                
                const tag = el.nodeName.toLowerCase();
                const role = el.getAttribute('role') || '';
                
                elements.push({
                    selector: getUniqueSelector(el),
                    tag: tag,
                    role: role,
                    zIndex: style.zIndex,
                    position: style.position,
                    opacity: style.opacity,
                    display: style.display,
                    transform: style.transform,
                    filter: style.filter,
                    backdropFilter: style.backdropFilter,
                    stackingPath: stackingPath,
                    domIndex: domIndex++
                });
                
                for (let child of el.children) {
                    walk(child);
                }
            }
            
            walk(document.body);
            return elements;
        }
        """
        
        elements = page.evaluate(js_code)
        browser.close()
        
        # Sort elements by stacking path and DOM index
        def get_sort_key(el):
            return (el['stackingPath'], el['domIndex'])
            
        sorted_elements = sorted(elements, key=get_sort_key)
        
        # Build the structured altitude map
        print("\n=== DOM STACKING ALTITUDE MAP (Low to High) ===")
        altitude_map = {}
        for el in sorted_elements:
            path_str = " -> ".join(map(str, el['stackingPath']))
            zlevel = f"[{path_str}]"
            
            style_details = f"{el['tag']}{':' + el['role'] if el['role'] else ''} (z-index: {el['zIndex']}, pos: {el['position']})"
            if el['opacity'] != '1':
                style_details += f" [opacity: {el['opacity']}]"
            if el['transform'] != 'none':
                style_details += " [transform]"
            if el['filter'] != 'none':
                style_details += " [filter]"
            if el['backdropFilter'] != 'none':
                style_details += " [backdrop-filter]"
                
            if zlevel not in altitude_map:
                altitude_map[zlevel] = {}
            altitude_map[zlevel][el['selector']] = style_details
            
        # Write report data
        output_data = []
        for el in sorted_elements:
            path_str = " -> ".join(map(str, el['stackingPath']))
            output_data.append({
                "zlevel": f"[{path_str}]",
                "selector": el['selector'],
                "tag": el['tag'],
                "role": el['role'],
                "zIndex": el['zIndex'],
                "position": el['position'],
                "opacity": el['opacity'],
                "transform": el['transform'],
                "filter": el['filter'],
                "backdropFilter": el['backdropFilter'],
                "stackingPath": el['stackingPath'],
                "domIndex": el['domIndex']
            })
            
        with open("stacking_report.json", "w") as f:
            json.dump(output_data, f, indent=2)
        print("Written raw stacking details to stacking_report.json")
        
        # Display sorted altitude map
        for zlevel, selectors in altitude_map.items():
            print(f"\nStacking Level: {zlevel}")
            for sel, details in selectors.items():
                print(f"  {sel} -> {details}")
                
if __name__ == "__main__":
    run_debug()
