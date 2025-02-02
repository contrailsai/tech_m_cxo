"use client"
import { useState } from "react";
import { useRouter } from 'next/navigation';

function ResponsiveTable({ table_data }) {

    //SAMPLE SAVED DATA for each scrape
    //_______________________
    // const table_data = [
    //     {
    //         "media_mongo_id": [
    //             "66e189a0992c10250c10aa64"
    //         ],
    //         "message": "Videos saved successfully",
    //         "success": true,
    //         "version": "v0.1",
    //         "video_count": 1,
    //         "video_sources": [
    //             "https://bit-360.site/design/t_quantumai/video/quantumai_en.mp4"
    //         ],
    //         "source_url": "https://bit-360.site"
    //     },
    // ]
    let sno = 0;

    return (
        <div className=" w-full flex flex-col gap-1">

            <div className=" text-xl w-full ml-5">
                Videos Scraped
            </div>
            <div className=" overflow-y-auto">

                <table className="w-full text-sm text-left  ">
                    <thead className=" bg-primary text-white sticky top-0">
                        <tr>
                            <th scope="col" className="px-6 py-3 ">
                                <span className="bg-primary font-normal inline-block">Sno</span>
                            </th>
                            <th scope="col" className="px-2 py-3 ">
                                <span className="bg-primary font-normal inline-block">Filename</span>
                            </th>
                            <th scope="col" className="px-2 py-3 ">
                                <span className="bg-primary font-normal inline-block">Video Source</span>
                            </th>
                            <th scope="col" className="px-2 py-3 ">
                                <span className="bg-primary font-normal inline-block">Source URL</span>
                            </th>
                        </tr>
                    </thead>
                    <tbody>
                        {table_data.length > 0 ?

                            (table_data.map((item, index) => {

                                if (item["video_count"] > 0) {
                                    return (<>
                                        {item["video_sources"].map((video, idx) => {
                                            const path = video.split('/')
                                            const filename = path[path.length - 1]
                                            sno += 1;
                                            return (
                                                <tr
                                                    key={`${index}-${idx}`}
                                                    className={`border-b ${index % 2 === 0 ? 'bg-white' : 'bg-slate-100'} hover:bg-gray-200 transition duration-150 ease-in-out `}
                                                >
                                                    <td className=" px-8 py-3 ">
                                                        {sno}
                                                    </td>
                                                    <td className=" pl-2  max-w-52 overflow-x-auto ">
                                                        {filename}
                                                    </td>
                                                    <td className=" pl-2  max-w-52 overflow-x-auto">
                                                        {video}
                                                    </td>
                                                    <td className=" px-2 max-w-52 overflow-x-auto">
                                                        <a href={item.source_url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                                                            {item.source_url}
                                                        </a>
                                                    </td>
                                                </tr>
                                            )
                                        })}
                                    </>)
                                }

                                else {
                                    sno += 1;
                                    return (
                                        <tr
                                            key={`${index}`}
                                            className={`border-b ${sno % 2 === 0 ? 'bg-white' : 'bg-slate-50'} hover:bg-gray-100 transition duration-150 ease-in-out `}
                                        >
                                            <td className="px-8 py-3">
                                                {sno}
                                            </td>
                                            <td className=" pl-2 max-w-52 overflow-x-auto ">
                                                -
                                            </td>
                                            <td className=" pl-2 max-w-52 overflow-x-auto">
                                                no video source found
                                            </td>
                                            <td className=" px-2 max-w-52 overflow-x-auto">
                                                <a href={item.source_url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                                                    {item.source_url}
                                                </a>
                                            </td>
                                        </tr>
                                    )
                                }
                            }))
                            :
                            (
                                <tr>
                                    <td colSpan="4" className="text-center py-16 text-lg text-black">No URLs Crawled</td>
                                </tr>
                            )

                        }
                    </tbody>
                </table>
            </div>
        </div>
    );
}

const Crawl_sites = ({ poi_id }) => {
    const router = useRouter();

    const [link, setlink] = useState("");

    const [results, set_results] = useState([]);
    const [loading, setLoading] = useState(false);
    const [mongodb_ids, set_mongodb_ids] = useState([]);

    const handle_scrape_start = async () => {
        setLoading(true);

        const options = {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                link: link,
            }),
        };
        // console.log(options)
        try {
            let response = await fetch(`https://api.contrails.ai/crawl`, options);
            if (!response.ok) {
                throw new Error(`Error: ${response.statusText}`);
            }
            let result = await response.json();
            // let result = {
            //     'video_sources': ['https://video-link/src/98345bdhs.mp4'],
            //     'video_count': 1,
            //     'media_mongo_id': ["sjhf48953___id"],
            //     'message': 'Videos saved successfully',
            //     'success': true,
            //     'version': "v0.1"
            // }
            result["source_url"] = link;

            console.log(result)
            if (result["media_mongo_ids"] != undefined)
                set_mongodb_ids(prevResults => [...prevResults, ...result["media_mongo_ids"]])
            set_results(prevResults => [...prevResults, result]);
        } catch (error) {
            console.error("Fetch error:", error);
        }
        setlink("");
        setLoading(false);
    }

    const start_deepfake_analysis = async () => {
        if (typeof (poi_id) !== 'string') {
            alert("NO POI Selected!")
            return;
        }
        const options = {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                media_ids: mongodb_ids,
                poi_id: poi_id
            }),
        };
        const result = await fetch(`https://api.contrails.ai/process-pending`, options);
        router.push('/cases');
    }

    return (
        <div className="w-full px-4 overflow-x-hidden ">
            <div className=' w-full text-2xl pb-2 '>
                Crawl Websites
            </div>
            <div className=" flex flex-col gap-3 items-end  ">
                {/* ADD URLS */}
                <form className=" w-full py-2 flex flex-col "
                    onSubmit={(e) => { e.preventDefault(); handle_scrape_start(); }}
                >
                    <label htmlFor="enter_url" className=" text-xl ml-4 mb-1 ">Enter Url</label>
                    <div className=" h-14 flex items-center gap-4 w-full px-2">
                        <input
                            type="url"
                            id="enter_url"
                            className=" border-b-2 border-primary outline-none px-4 py-3 focus:py-1 bg-white transition-all w-4/5"
                            placeholder="Type a url like https://website.link/to-crawl"
                            value={link}
                            onChange={(e) => { setlink(e.target.value) }}
                            required
                        />
                        <button className={` w-1/5 border border-primary ${loading ? "bg-primary text-white" : "bg-white hover:bg-primary text-primary hover:text-white"}  h-fit py-2 px-4 flex justify-center gap-3 transition-all `}>
                            Start Crawl
                            {loading &&
                                (
                                    <div role="status">
                                        {/* LOADING */}
                                        <svg aria-hidden="true" className="w-4 h-6  animate-spin fill-primary" viewBox="0 0 100 101" fill="none" xmlns="http://www.w3.org/2000/svg">
                                            <path d="M100 50.5908C100 78.2051 77.6142 100.591 50 100.591C22.3858 100.591 0 78.2051 0 50.5908C0 22.9766 22.3858 0.59082 50 0.59082C77.6142 0.59082 100 22.9766 100 50.5908ZM9.08144 50.5908C9.08144 73.1895 27.4013 91.5094 50 91.5094C72.5987 91.5094 90.9186 73.1895 90.9186 50.5908C90.9186 27.9921 72.5987 9.67226 50 9.67226C27.4013 9.67226 9.08144 27.9921 9.08144 50.5908Z" fill="currentColor" />
                                            <path d="M93.9676 39.0409C96.393 38.4038 97.8624 35.9116 97.0079 33.5539C95.2932 28.8227 92.871 24.3692 89.8167 20.348C85.8452 15.1192 80.8826 10.7238 75.2124 7.41289C69.5422 4.10194 63.2754 1.94025 56.7698 1.05124C51.7666 0.367541 46.6976 0.446843 41.7345 1.27873C39.2613 1.69328 37.813 4.19778 38.4501 6.62326C39.0873 9.04874 41.5694 10.4717 44.0505 10.1071C47.8511 9.54855 51.7191 9.52689 55.5402 10.0491C60.8642 10.7766 65.9928 12.5457 70.6331 15.2552C75.2735 17.9648 79.3347 21.5619 82.5849 25.841C84.9175 28.9121 86.7997 32.2913 88.1811 35.8758C89.083 38.2158 91.5421 39.6781 93.9676 39.0409Z" fill="currentFill" />
                                        </svg>
                                    </div>
                                )
                            }
                        </button>
                    </div>
                </form>
                <div className="w-full overflow-y-auto overflow-x-hidden min-h-80 ">
                    <ResponsiveTable table_data={results} />
                </div>
                {/* START ANALYSIS */}
                <div
                    onClick={() => {
                        if( (mongodb_ids.length>0) && (typeof(poi_id)==='string') ){
                            start_deepfake_analysis();
                        }
                    }}
                    className={` ${ (mongodb_ids.length>0 && typeof(poi_id)==='string') ? ' cursor-pointer': 'cursor-not-allowed'} border-2 border-primary  bg-primary my-2 py-2 px-8 mx-auto text-lg text-white w-fit `}
                >
                    Start deepfake analysis
                </div>
            </div>
        </div>
    )
}

export default Crawl_sites;