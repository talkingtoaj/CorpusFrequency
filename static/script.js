// Persist checkbox state. The checkbox marks an n-gram as one the user wants
// to keep; that is deliberately independent of whether an example sentence
// has been chosen for it yet, so the two can be filled in in either order.
document.querySelectorAll('.ngram-checkbox').forEach(checkbox => {
    checkbox.addEventListener('change', event => {
        const ngram = checkbox.dataset.ngram
        const selected = event.target.checked

        const body = new URLSearchParams({ ngram: ngram, selected: selected })
        fetch('/toggle-selected', {
            method: 'POST',
            headers: { 'Content-type': 'application/x-www-form-urlencoded' },
            body: body,
        }).catch(() => {
            // Roll the checkbox back so it never shows state the server
            // did not actually record.
            event.target.checked = !selected
        })
    })
})
