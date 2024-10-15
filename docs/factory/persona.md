# PersonaPipeline

`PersonaPipeline` is a class that creates a pipeline for generating personas based on a simulation description.

## Overview

This pipeline generates personas by creating random variables that fit into the simulation description and then generating a backstory for each sample. The number of samples can be specified to determine the number of personas to be generated.


```python
import asyncio
import os

from dria.client import Dria
from dria.factory import PersonaPipeline
from dria.pipelines import PipelineConfig

dria = Dria(rpc_token=os.environ["DRIA_RPC_TOKEN"])


async def evaluate():
    await dria.initialize()
    pipeline = PersonaPipeline(dria, PipelineConfig()).build(simulation_description="The cyberpunk city in the year of 2077.", num_samples=2)
    res = await pipeline.execute(return_output=True)
    print(res)


if __name__ == "__main__":
    asyncio.run(evaluate())
```

Expected output

```json
[
   {
      "backstory":[
         "In the neon-drenched and polluted streets of Neo-Tokyo, Aiko Sánchez, a 78-year-old Hispanic mercenary with Japanese ancestry, has lived her life on the fringes of society. Born in the sprawling Slum District, Aiko grew up witnessing the harsh realities of poverty and oppression firsthand. To survive, she turned to cybernetic enhancements, opting for five levels of augmentation that allowed her to perform physically demanding tasks without succumbing to fatigue or injury—though these enhancements came at a cost: they were obtained through questionable means and often in secret. Aiko\\'s loyalty to the Resistance Movement is mixed; while she has dedicated many years to their cause, her past as a mercenary for hire occasionally tempts her towards more personal gain. Her current status as divorced reflects not only her tumultuous personal life but also the toll that her work has taken on her relationships. Despite having a criminal record, Aiko prefers minimal tech in her daily life, relying instead on her enhanced physical abilities and street smarts to navigate the dangers of Neo-Tokyo. As she continues to fight against the oppressive corporations that dominate the city, Aiko struggles with balancing her commitment to the Resistance Movement"
      ]
   },
   {
      "backstory":[
         "Born to an African immigrant family in Downtown, Alex grew up in a vibrant but gritty neighborhood where technology and tradition blended seamlessly with the hustle of everyday life. Despite the challenges faced by many in his community, Alex's entrepreneurial spirit thrived early on, leading him to establish himself as a street vendor in downtown marketplaces by age 20. His success was fueled not only by adaptability but also by a series of cybernetic enhancements that began at an early age, starting with minor augmentations and culminating in the sophisticated level-4 implants that now seamlessly integrate into his daily operations. Alex's loyalty to the Corporate Faction, where he leverages both traditional tech and advanced cybernetics, reflects his pragmatic approach to navigating the complex socio-economic landscape of 2077. His criminal record, a byproduct of several past endeavors to secure better opportunities for himself and his family, underscores his willingness to take risks in pursuit of success. Alex is fluent in Mandarin, allowing him to connect deeply with the diverse community that frequents his stall, selling everything from tech accessories to vintage collectibles."
      ]
   }
]
```