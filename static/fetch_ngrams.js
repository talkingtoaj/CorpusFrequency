async function fetchNgramsGroups() {
    try{
        const response = await fetch("/api/ngram-groups");
    const data = await response.json();
    
    console.log('ngram_groups:', data);
  
    const checkboxes = document.querySelectorAll("input[type='checkbox']");    //Get all checkboxes

    Object.entries(data).forEach(([n, group])=>{
        //loop through the API for ngram and invariably for chosen_text//
        console.log(`\nN-gram size ${n}:`);
        //for each ngram in the group
        Object.entries(group).forEach(([ngram, info])=>{
            //find the checkbox that corresponds to this ngram 
            const checkbox = Array.from(checkboxes).find(cb => {
                const link = cb.nextElementSibling;
                return link && link.textContent.includes(ngram);
            })
            //set checkbox state based on chosen text availability//
            if (checkbox){
                if (info.chosen_text){
                    checkbox.checked = true;
                    console.log(`${ngram}: "${info.chosen_text}`);
                } else {
                    checkbox.checked = false
                }

            }
    
           
           
        });
    });
    }catch(error){
        console.error("Error fetching ngram groups:", error);
    }

}

fetchNgramsGroups()

