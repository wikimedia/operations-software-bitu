//# SPDX-License-Identifier: GPL-3.0-or-later

/*
Wait for document content to load, before attaching
event handlers.
*/
document.addEventListener('DOMContentLoaded', function() {

    // Add handler for dismissing wmf account link request.
    const removable_elements = document.getElementsByClassName('delete');

    for (element of removable_elements) {
        element.onclick = function(event){
            parent = event.srcElement.parentElement.parentElement
            parent.remove();

            /* Get classList array iterator, convert to array and check for
               for membership */
            if ([...parent.classList.values()].indexOf('is-wmf_link') > 0) {
                document.cookie = "wmf_link=no; path=/; SameSite=Strict";
            }
        };
    }
}, false);