const checkboxes = document.querySelectorAll('.checkbox');

checkboxes.forEach(checkbox => {
    checkbox.addEventListener('change', (event) => {
        // Get the ngram-link that's a sibling of this checkbox
        const ngramLink = checkbox.nextElementSibling;
        const ngramText = ngramLink.textContent.split(' - ')[0]; // Extract just the ngram
        
        // Get or create the paragraph element
        let ngramSentence = ngramLink.nextElementSibling;
        
        if (event.target.checked) {
            // Create the paragraph if it doesn't exist
            if (!ngramSentence || ngramSentence.tagName !== 'P') {
                ngramSentence = document.createElement("p");
                ngramSentence.textContent = `Sentences containing ${ngramText} will be displayed here.`;
                ngramLink.parentElement.appendChild(ngramSentence);
            } else {
                ngramSentence.style.display = 'block';
            }
        } else {
            // Hide the paragraph instead of removing it
            if (ngramSentence && ngramSentence.tagName === 'P') {
                ngramSentence.style.display = 'none';
            }
        }
    });
});