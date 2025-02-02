export const dynamic = 'force-dynamic'

import Data_table from "./Data_table";
import {get_mongo_result_data, get_s3_view_url, delete_media} from "@/lib/data";

const Page = async ()=>{
    const data = await get_mongo_result_data();

    data.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));

    for(let i=0; i<data.length; i++){
        data[i]["view_url"] = await get_s3_view_url(data[i]["s3_key"]);
    }   
      
    return (
        <div className=" w-full">
            {/* <Show_data data={data} /> */}
            <Data_table delete_media={delete_media} data={data} />
        </div>
    )
}

export default Page