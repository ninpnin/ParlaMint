# Feedback – ParlaMint SE

_Väinö Yrjänäinen_

Based on the experiences of ParlaMint SE, here are some thoughts on how the  process could be improved for new participants.

## Test and pull request procedure

There are multiple parts to the requirements

1. Parla-Clarin/ParlaMint schema validation
2. Additional ParlaMint requirements
3. Linguistic annotation and ana.tei files
4. Conversion to other formats

Working with a new corpus, it's the easiest to start with conforming to the schema (1), when that's done, move on to making sure the other peculiarities of ParlaMint are in place (2), and then implement the linguistic annotation (3). Then, if there are issues with conversion into other formats, they can be fixed (4). AFAIK this may be suggested somewhere in the documentation already.

This should be reflected in the test suite. It makes it easier for the participants to build the corpus, and also for ParlaMint to track progress of each country's project. Moreover, you get people to do the work in smaller, more manageable subprojects.

It might also be good to be able to merge earlier, upon the firsts tests passing. This keeps country projects from doing their work isolated on their side, which makes it harder to eg. catch errors or missing things in the tests.

## Giving feedback

Giving feedback should be more structured. Currently some of the comments just poured in randomly, which added to the workload. Moreover, many problems that were only reported after the second or third sample submission were also already present in the first submission.

Suggestion for an iterative, yet structured loop

1. Country project submits a new sample
2. Country project requests for feedback
3. ParlaMint project goes over the sample
4. ParlaMint project writes issues with current sample, or
5. ParlaMint project tells that country project can proceed to next step

To be fair, something along these lines was already partially in place.

## Demoing the infrastructure via Zoom or video

Currently, the project assumes people to know how to run the validation by reading README.md and CONTRIBUTING.md. While all/most relevant information technically exists in those documents, it would be good to demonstrate how it works in practice. This would save 20+ projects' time with relatively little effort, after all.

This might be done via a short Zoom workshop, which could also be recorded.

Apologies if I had missed this and this already exists. However, it was at least not recorded, so that could be done for the next participants.

## Last words

Lastly, I want to underline that going through all the hoops and loops of the corpus creation and validation did yield a great end product. I appreciate the work that has been put into this project, and want make international collaboration like this easier in the future.

Best regards,
Väinö Yrjänäinen
