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
    // Sort checkboxes: unchecked on top and checked below 
    const allCheckboxDivs = document.querySelectorAll("input[type='checkbox']");
    const divElements = Array.from(allCheckboxDivs).map(cb => cb.parentElement);


    //Sort: unchecked (false) comes before checked 
    divElements.sort((a,b)=>{
        const aChecked = a.querySelector("input[type='checkbox']").checked;
        const bChecked = b.querySelector("input[type='checkbox']").checked
        return aChecked - bChecked //false(0) comes before true(1)
    })

    //Re-append sorted divs to the parent in new order 
    const parent = divElements[0].parentElement;
    divElements.forEach(div => parent.appendChild(div))
    }catch(error){
        console.error("Error fetching ngram groups:", error);
    }

}

fetchNgramsGroups()

