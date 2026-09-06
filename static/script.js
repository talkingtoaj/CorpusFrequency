// Persist checkbox state. The checkbox marks an n-gram as one the user wants
// to keep, which is deliberately independent of whether an example sentence
// has been written for it yet - so the two can be filled in in either order.
const csrfToken = document.querySelector('#csrf-holder [name=csrfmiddlewaretoken]').value

document.querySelectorAll('.ngram-checkbox').forEach(checkbox => {
    checkbox.addEventListener('change', async event => {
        const selected = event.target.checked
        try {
            const response = await fetch(checkbox.dataset.url, {
                method: 'POST',
                headers: {
                    'Content-type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': csrfToken,
                },
                body: new URLSearchParams({ selected: selected }),
            })
            if (!response.ok) throw new Error(response.statusText)
        } catch (error) {
            // Never leave the box showing state the server did not record.
            event.target.checked = !selected
        }
    })
})
