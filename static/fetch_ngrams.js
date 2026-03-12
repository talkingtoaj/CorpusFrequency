async function fetchNgramsGroups() {
    try{
        const response = await fetch("/api/ngram-groups");
    const data = await response.json();
    
    console.log('ngram_groups:', data);
  
 

    Object.entries(data).forEach(([n, group])=>{
        console.log(`\nN-gram size ${n}:`);
        Object.entries(group).forEach(([ngram, info])=>{
           if (info.chosen_text) {
            console.log(`${ngram}: "${info.chosen_text}"`)
           }
        });
    });
    }catch(error){
        console.error("Error fetching ngram groups:", error);
    }

}

fetchNgramsGroups()