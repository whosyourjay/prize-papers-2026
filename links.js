const paperLinks = {
  "aks-modern": [
    "https://web.archive.org/web/20240419074127/",
    "https://www.cs.tau.ac.il/~amnon/Classes/2019-Derandomization/",
    "Lectures/Lecture7-AKS-All.pdf",
  ].join(""),
  "relativization-modern": [
    "https://ocw.mit.edu/courses/",
    "18-405j-advanced-complexity-theory-spring-2016/",
    "95da3f6c4aebf07a34e6dca91861f1c7_MIT18_405JS16_Relativ.pdf",
  ].join(""),
  "independence-modern-one": [
    "https://www.cs.columbia.edu/~rocco/Teaching/S24/Scribe/",
    "2024-03-19-scribe-notes.pdf",
  ].join(""),
  "independence-modern-two": [
    "https://www.cs.columbia.edu/~rocco/Teaching/S24/Scribe/",
    "2024-03-26-scribe-notes.pdf",
  ].join(""),
};

for (const link of document.querySelectorAll("[data-paper]")) {
  link.href = paperLinks[link.dataset.paper];
}
