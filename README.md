## A comparative account of intransitive verbs with conservative first person forms in Cariban 
This repo contains data, code, and manuscript for a diachronic and functional study of verbs with conservative first person markers in 9 Cariban languages.

[![CC BY-SA 4.0][cc-by-sa-shield]][cc-by-sa]

Nine Cariban languages have a group of intransitive verbs irregularly inflected for first person.
The irregular first person markers are conservative, contrasting with innovative regular markers.
They are a result of person marker extensions not affecting some verbs, which happened independently in six (proto-)languages.
These six incomplete extensions left between one and seven conservatively inflected verbs, which show a great etymological overlap across (proto-)languages.
Bybee's network model of morphology was used to generate hypotheses about factors causing the distribution of conservative and innovative markers in each language.
Predictions of different possible factors were then tested against the data.
Because of patterns reconstructible to Proto-Cariban, the hypothesized factors largely overlap in their predictions, though phonology (combined with frequency) shows a strong overall performance.

More info about the study in general can be found here:

* [Slides for the SLE 2021](documents/talks_abstracts/carib_irreg_SLE.pdf)
* [Current draft of manuscript](documents/cariban_underived.pdf)

This repository is organized as follows:

* [data](data) contains all the data on which the analyses in the paper are based
	* [cldf](data/cldf) is a [CLDF](https://cldf.clld.org/) version of the dataset
* [workflow](workflow) contains different python scripts used for analysis, data visualization, and CLDF dataset creation.
	* [data_output](workflow/data_output) contains tables with the qualitative and quantitative results
* [documents](documents) contains the current version of the manuscript as well as materials used in presentations.

[cc-by-sa-shield]: https://img.shields.io/badge/License-CC%20BY--SA%204.0-lightgrey.svg
[cc-by-sa]: http://creativecommons.org/licenses/by-sa/4.0/