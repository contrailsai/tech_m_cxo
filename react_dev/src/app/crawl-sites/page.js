"use client"
import Link from "next/link";
import { useState } from "react";
const page = () => {

    const [links_list, setlinks_list] = useState([]);
    const [link, setlink] = useState("");

    const [result, set_result] = useState()

    const handle_scrape_start = async () => {
        for (let i = 0; i < links_list.length; i++) {

            const options = {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    link: links_list[i]
                }),
            };
            const result = await fetch(`https://api.contrails.ai/add-crawler-link`, options);
        }

        const result = await fetch(`https://api.contrails.ai/scrape-crawler-videos`);
        set_result(result);
    }
    const start_deepfake_analysis = ()=>{
        
    }
    return (
        <div className="">
            <div className=' w-full flex justify-between px-10 items-center '>
                <div className=' text-3xl py-2 px-12'>
                    Crawl Websites
                </div>
            </div>
            <div className=" flex items-start justify-between ">
                <form
                    onSubmit={(e) => { e.preventDefault(); setlinks_list([...links_list, link]); setlink("") }}
                    action=""
                    className=" min-w-96 px-12"
                >
                    <div className=" my-4 py-4 mx-10 px-4 shadow-primary shadow w-fit rounded-lg flex flex-col items-center ">
                        <div className=' text-xl pb-4 w-full'>
                            Links to Add
                        </div>

                        <div className=" pb-5">
                            <label htmlFor="" className=" ">Enter Link</label>
                            <input
                                type="url"
                                name=""
                                id=""
                                className=" mx-4 rounded bg-slate-200 px-2 py-1 outline-slate-300 transition-all"
                                value={link}
                                onChange={(e) => { setlink(e.target.value) }}
                            />
                        </div>

                        <button className=" w-fit bg-primary text-slate-100 px-6 py-2 rounded-full" type="submit">
                            Add
                        </button>
                    </div>
                </form>

                <div className=" min-w-96 px-4  py-4 my-4 mx-32 shadow-primary shadow w-fit rounded-lg flex flex-col items-center ">
                    <div className=" text-xl px-4 w-full ">
                        Links to Crawl
                    </div>
                    <div className=" w-full flex flex-col px-4 py-4 gap-2 ">
                        {
                            links_list.length !== 0 ?
                                (links_list.map((val, idx) => {
                                    return (
                                        <div key={idx}>
                                            {idx + 1}. {val}
                                        </div>
                                    )
                                })
                                ) :
                                (
                                    <>
                                        <div className=" flex items-center justify-center py-10">
                                            NO LINKS
                                        </div>
                                    </>
                                )
                        }
                    </div>
                    <div onClick={() => { handle_scrape_start() }} className=" bg-primary py-2 px-4 cursor-pointer rounded-full text-slate-100 w-fit">
                        Start Scrapping
                    </div>
                </div>
            </div>

            {
                result &&
                (
                    <div>
                        <div className=" text-2xl">
                            SCRAPE RESULT
                        </div>
                        {
                            Object.keys(result.source_data).map((key, idx) => {
                                return (
                                    <div className=" flex gap-4 ">
                                        <div className=" font-semibold">
                                            {key} :
                                        </div>
                                        <div>
                                            {result.source_data[key]}
                                        </div>
                                    </div>
                                )
                            })
                        }
                        <div onClick={() => { start_deepfake_analysis() }} className=" bg-primary py-2 px-4 cursor-pointer rounded-full text-slate-100 w-fit">
                            Start deepfake analysis
                        </div>
                    </div>
                )
            }
        </div>
    )
}

export default page;