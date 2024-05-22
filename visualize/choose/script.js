const list = document.getElementById("list");
const tagsContainer = document.getElementById("tags");

let selectedOption = "medium";

list.addEventListener("click", (e) => {
    if (e.target.type === "radio") {
        selectedOption = e.target.value;
        $("#list li").removeAttr("style")//css({"background":"#eee"})
        $(e.target.parentElement).css({ "border": "5 px solid red" })
        updateTags();
    }
});

connections_count = Object.assign({}, ...DATA.nodes.map(
    node => ({ [node.id]: (node.size - 10) * 2 })
));


function updateTags() {
    tagsContainer.innerHTML = "";

    let tags = [];
    switch (selectedOption) {
        case "small":
            tags = Object.keys(connections_count).filter(node => connections_count[node] > 50);
            break;
        case "medium":
            tags = ["Erster Weltkrieg", "Zweiter Weltkrieg"];
            break;
        case "large":
            tags = [];
            break;
        default:
            return;
    }

    tags.forEach((tag) => {
        const tagElement = document.createElement("div");
        tagElement.className = "tag";
        tagElement.textContent = tag;
        tagElement.addEventListener("click", () => {
            tagElement.remove();
        });
        tagsContainer.appendChild(tagElement);
    });
}

updateTags()