import clientPromise from "@/lib/mongodb"
import Show_data from "./show_data"

const page = async ()=>{

    const get_mongo_result_data = async ()=>{
        "use server"
        const client = await clientPromise;
        const db = client.db('poi_demo'); 
        const collection = db.collection('media');

        const data = await collection.find({}).toArray();  
        return data
    }

    const data = await get_mongo_result_data()

    return (
        <div className="">
            <Show_data data={data} />
        </div>
    )
}

export default page