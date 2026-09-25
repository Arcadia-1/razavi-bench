// Shared by every page that shows costs, so they all price a run the same way.
// API prices per 1M tokens: [input, output, cached]. Add new models here; every page reads this file.
var PRICE={
  claude_opus_55:[4,20,0.2], claude_fable_51:[10,50,0.25],
  claude_opus_5:[5,25,0.5], claude_fable_5:[10,50,1], claude_opus_48:[5,25,0.5], claude_sonnet_46:[3,15,0.3],
  gpt_6_astra:[10,50,1], gpt_6_sol:[2,10,0.2],
  gpt_56:[5,30,0.5], gpt_56_terra:[2,12,0.2], gpt_56_luna:[0.2,1.2,0.02],
  gpt_55:[5,30,0.5], gpt_53:[1.75,14,0.175], gpt_52:[1.75,14,0.175],
  gpt_54_thinking_high:[2.5,15,0.25], gpt_54_mini:[0.75,4.5,0.075], gpt_4o:[2.5,10,0.25],
  qwen_38_max:[1,6,0.1], qwen_38_27b:[0.4,3,0.08], gemini_35_flash:[1.5,9,0.15], gemini_36_flash:[1.5,7.5,0.15],
  gemini_37_flash:[0.375,1.875,0.0375], gemini_31:[2,12,0.2],
  grok_45:[2,6,0.5], grok_46:[2,6,0.5], doubao_seed_21_pro:[0.88,4.42,0.088],
  kimi_k3:[3,15,0.3], kimi_k27:[0.95,4,0.19], minimax_m3:[0.6,2.4,0.06], inkling_small:[0.5,1.2,0.12],
  qwen_37_plus:[0.32,1.28,0.064], qwen_37_flash:[0.03,0.13,0.006], step_37_flash:[0.2,1.15,0.02],
  inkling:[1,4.05,0.2], gemma_4_31b_it:[0.09,0.34,0.018], llama_4_maverick:[0.2,0.8,0.04],
  muse_spark_12:[1.25,4.25,0.15],
  gpt_5:[1.25,10,0.125], gpt_4o_mini:[0.15,0.6,0.075],
  gemini_25_pro:[1.25,12,0.125], gemini_25_flash_lite:[0.1,0.4,0.01],
  claude_sonnet_4:[3,15,0.3], claude_haiku_45:[1,5,0.2],
  qwen25_vl_72b_instruct:[0.8,1,0.8], qwen3_vl_235b_a22b_instruct:[0.21,1.9,0.21]
};
// Self-hosted checkpoints retain token accounting but have no comparable API bill.
var NO_API_COST={qwen_38_27b:true};
function computeCost(modelKey,tk){if(NO_API_COST[modelKey])return null;var p=PRICE[modelKey];if(!p&&modelKey){var keys=Object.keys(PRICE);for(var i=0;i<keys.length;i++){if(modelKey.indexOf(keys[i])===0){p=PRICE[keys[i]];break;}}}if(!p||!tk)return null;var cached=tk.cached_input_tokens||0;var cost=((tk.input_tokens-cached)*p[0]+cached*p[2]+tk.output_tokens*p[1])/1e6;return Math.round(cost*100)/100;}
