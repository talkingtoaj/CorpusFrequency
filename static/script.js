// Behaviour for the n-gram triage table.
//
// Two jobs: persist a checkbox the moment it changes, and make the table
// navigable from the keyboard. Someone working through several thousand
// n-grams with a mouse is doing hours of avoidable work, so j/k/space/enter
// are treated as the primary interface rather than a convenience.

const csrfHolder = document.querySelector('#csrf-holder [name=csrfmiddlewaretoken]')
const csrfToken = csrfHolder ? csrfHolder.value : ''

/* ------------------------------------------------------------------ *
 * Persisting a selection
 * ------------------------------------------------------------------ */

async function persist(checkbox) {
    const selected = checkbox.checked
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
        checkbox.checked = !selected
    }
}

document.querySelectorAll('.ngram-checkbox').forEach(checkbox => {
    checkbox.addEventListener('change', () => persist(checkbox))
})

/* ------------------------------------------------------------------ *
 * Keyboard triage
 * ------------------------------------------------------------------ */

const rows = Array.from(document.querySelectorAll('.ngram-row'))
let activeIndex = -1

function setActive(index) {
    if (!rows.length) return
    // Clamp rather than wrap: running off the end of a page should stop, not
    // silently jump back to the top of a list you have already worked through.
    const next = Math.max(0, Math.min(index, rows.length - 1))
    rows.forEach(row => row.classList.remove('is-active'))
    activeIndex = next
    const row = rows[next]
    row.classList.add('is-active')
    row.scrollIntoView({ block: 'nearest' })
}

function isTyping(target) {
    return target.matches('input, textarea, select')
}

document.addEventListener('keydown', event => {
    if (event.ctrlKey || event.metaKey || event.altKey) return

    // '/' focuses the filter box from anywhere on the page.
    if (event.key === '/' && !isTyping(event.target)) {
        const filter = document.getElementById('filter-input')
        if (filter) {
            event.preventDefault()
            filter.focus()
            filter.select()
        }
        return
    }

    if (event.key === 'Escape' && isTyping(event.target)) {
        event.target.blur()
        return
    }

    if (!rows.length || isTyping(event.target)) return

    switch (event.key) {
        case 'j':
        case 'ArrowDown':
            event.preventDefault()
            setActive(activeIndex + 1)
            break
        case 'k':
        case 'ArrowUp':
            event.preventDefault()
            setActive(activeIndex <= 0 ? 0 : activeIndex - 1)
            break
        case ' ': {
            if (activeIndex < 0) return
            event.preventDefault()
            const checkbox = rows[activeIndex].querySelector('.ngram-checkbox')
            checkbox.checked = !checkbox.checked
            persist(checkbox)
            break
        }
        case 'Enter':
            if (activeIndex < 0) return
            event.preventDefault()
            window.location = rows[activeIndex].dataset.href
            break
    }
})

// Clicking anywhere on a row selects it as the active one, so the mouse and
// the keyboard stay in agreement about where you are.
rows.forEach((row, index) => {
    row.addEventListener('click', event => {
        if (event.target.closest('a, input, label')) return
        setActive(index)
    })
})

/* ------------------------------------------------------------------ *
 * Pending state on slow submissions
 * ------------------------------------------------------------------ */

// Analysis and upload both block for as long as they take. Without feedback
// the page looks inert and people click the button a second time.
document.querySelectorAll('form[data-pending]').forEach(form => {
    form.addEventListener('submit', () => {
        const button = form.querySelector('button[type=submit]')
        if (!button) return
        button.setAttribute('aria-busy', 'true')
        button.disabled = true
        button.textContent = form.dataset.pending
    })
})
