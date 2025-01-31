"use client"
import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';

//SAMPLE DATA
//______________________________________________________
// const data = [
//     {
//         "_id": "672ccff772b95a743ad884d7",
//         "source_url": "https://systemaibasis.top/",
//         "upload_status": "completed",
//         "s3_key": "systemaibasis_top/raw/66db06360f5a2f74944465db.mp4",
//         "created_at": "2024-11-07 20:04:31.044000",
//         "contentType": "video/mp4",
//         "file_name": "kazmunay-preland.mp4",
//         "processing_status": "done",
//         "prediction": "real",
//         "results": [
//             {
//                 "raw_video_path": "systemaibasis_top/raw/66db06360f5a2f74944465db.mp4",
//                 "clip_path": "systemaibasis_top/preprocessed/66db06360f5a2f74944465db.mp4/clip_0.mp4",
//                 "frame": "fake",
//                 "audio": "fake",
//             },
//             {
//                 "raw_video_path": "systemaibasis_top/raw/66db06360f5a2f74944465db.mp4",
//                 "clip_path": "systemaibasis_top/preprocessed/66db06360f5a2f74944465db.mp4/clip_1.mp4",
//                 "frame": "fake",
//                 "audio": "real",
//             },
//             {
//                 "raw_video_path": "systemaibasis_top/raw/66db06360f5a2f74944465db.mp4",
//                 "clip_path": "systemaibasis_top/preprocessed/66db06360f5a2f74944465db.mp4/clip_2.mp4",
//                 "frame": "real",
//                 "audio": "real",
//             }
//         ]
//     },
// ];

export default function Data_table({ delete_media, data }) {
    const [openIndex, setOpenIndex] = useState(null);
    const [poi, setpoi] = useState(null);
    const [deleted, set_deleted] = useState([]);

    const toggleDropdown = (index) => {
        setOpenIndex(openIndex === index ? null : index);
    };

    const formatDate = (dateString) => {
        const date = new Date(dateString);
        // dd/mm/yy
        return `${date.getDate()}/${date.getMonth() + 1}/${date.getFullYear()}`;
    };

    useEffect(() => {
        const get_poi_data = async () => {
            if (openIndex !== null) {
                const poiId = data[openIndex]?.poi_id;
                if (poiId) {
                    try {
                        const response = await fetch(`/api/get_poi?poi_id=${poiId}`);
                        if (!response.ok) throw new Error("Failed to fetch POI data");
                        const poiData = await response.json();
                        setpoi(poiData);
                    } catch (error) {
                        console.error("Error fetching POI:", error);
                    }
                } else {
                    setpoi(null);
                }
            }
            else {
                setpoi(null);
            }
        };
        get_poi_data();
    }, [openIndex]);

    const handle_analysis_deletion = () => {

        let del_success = delete_media(data[openIndex]["_id"], data[openIndex]["s3_key"]);

        if (del_success) {
            toggleDropdown();
            set_deleted([...deleted, data[openIndex]['_id']])
        }
    }
    return (
        <div className="container mx-auto p-4">
            <div className="bg-primary rounded-full py-4 mb-4 hidden md:block px-8">
                <div className="grid grid-cols-12 gap-2 text-slate-200 text-sm">
                    <div className="col-span-1">S.No</div>
                    <div className="col-span-2">Filename</div>
                    <div className="col-span-1">Status</div>
                    <div className="col-span-1">Prediction</div>
                    <div className="col-span-3">Source URL</div>
                    <div className="col-span-3">Created At</div>
                    <div className="col-span-1">Actions</div>
                </div>
            </div>
            {data.map((item, index) => {
                if( deleted.includes(item['_id']) ){
                    return (<></>)
                }
                return (
                    <div key={index} className=" border-b ">
                        {/* ROW DETAILS */}
                        <div className="bg-white hover:bg-slate-100 rounded-full px-8 py-6 transition-all ">
                            <div className="grid grid-cols-1 md:grid-cols-12 gap-2 items-center">
                                <div className="md:col-span-1 font-semibold text-center md:text-left">
                                    <span className="inline-block bg-slate-200 rounded-full px-3 py-1 text-xs md:text-sm">
                                        {index + 1}
                                    </span>
                                </div>
                                <div className="md:col-span-2 truncate">{item.file_name}</div>
                                <div className="md:col-span-1 ">
                                    <span className="bg-blue-100 bg-primary/20 px-3 py-1 rounded-full text-xs">
                                        {item.processing_status}
                                    </span>
                                </div>
                                <div className="md:col-span-1">
                                    {
                                        item.prediction === undefined ?
                                            (
                                                <span className={`px-4 py-1 rounded-full text-xs`}>
                                                    ---
                                                </span>)
                                            :
                                            (
                                                <span className={`px-4 py-1 rounded-full text-xs ${(item.prediction === 'real' || item.prediction === 'no poi') ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                                                    {item.prediction}
                                                </span>
                                            )
                                    }
                                </div>
                                <Link href={item.source_url} className="md:col-span-3 hover:underline truncate text-xs md:text-sm">{item.source_url}</Link>
                                <div className="md:col-span-3 text-xs md:text-sm">{formatDate(item.created_at)}</div>
                                <div className="md:col-span-1 px-3">
                                    <button
                                        onClick={() => toggleDropdown(index)}
                                        className="bg-slate-200 hover:bg-slate-300 rounded-full p-2 focus:outline-none"
                                        aria-label={openIndex === index ? "Close details" : "Open details"}
                                    >
                                        <div className={` ${openIndex === index ? "rotate-180" : "  "} transition-all `} >
                                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1} stroke="currentColor" className="size-5">
                                                <path strokeLinecap="round" strokeLinejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5" />
                                            </svg>
                                        </div>
                                    </button>
                                </div>
                            </div>
                        </div>
                        {/* DROP DOWN */}
                        {openIndex === index && (
                            <div className="mt-4 p-4  rounded-3xl shadow-inner shadow-primary flex w-full justify-between">
                                {/* POI DETAILS */}
                                {
                                    poi !== null ?
                                        <div className=' w-fit min-w-52'>
                                            <div className='text-lg font-semibold '>
                                                Person Searched :
                                            </div>
                                            <div className='flex items-center gap-5 my-5'>
                                                <Image className='rounded-full' src={poi.img_url} width={75} height={75} />
                                                <div className=' text-lg '>
                                                    {poi.name}
                                                </div>
                                            </div>
                                        </div>
                                        :
                                        <>
                                        </>
                                }

                                {/* for video  */}
                                <div className=' w-full  flex justify-center overflow-hidden rounded-3xl'>
                                    <video
                                        src={item["view_url"]}
                                        controls
                                        className='max-h-72 rounded-xl'
                                    />
                                </div>

                                {/* RESULT */}
                                <div className=' w-full flex flex-col items-center justify-between gap-4'>
                                    <div className='mx-auto'>
                                        {
                                            (item.results === undefined) ?
                                                (
                                                    <div className='w-full text-xl text-center py-4 '>
                                                        This file is queued for analysis
                                                    </div>
                                                )
                                                :
                                                (
                                                    <>
                                                        {/* for Clips data */}
                                                        <div className='min-w-96 border px-2 rounded-3xl '>
                                                            {
                                                                item.results.length === 0 ?
                                                                    <div className='w-full text-xl text-center py-4 '>
                                                                        Video doesn&apos;t contain the requested POI
                                                                    </div>
                                                                    :

                                                                    <div className='flex px-3'>
                                                                        <h3 className="w-full text-lg font-semibold mb-4 pt-4 pb-2 px-4">Clip Detail</h3>
                                                                        {
                                                                            item.results[0].final_clip_result ?
                                                                                <>
                                                                                    <h3 className="text-lg font-semibold mb-4 pt-4 pb-2 px-4">Prediction</h3>
                                                                                </>
                                                                                :
                                                                                <>
                                                                                    <h3 className="text-lg font-semibold mb-4 pt-4 pb-2 px-4">Frame</h3>
                                                                                    <h3 className="text-lg font-semibold mb-4 mr-2 pt-4 pb-2 px-4">Audio</h3>
                                                                                </>
                                                                        }
                                                                    </div>
                                                            }

                                                            <div className=" divide-y-2 max-h-80 overflow-y-auto  ">
                                                                {
                                                                    item.results.map((clip, clipIndex) => (
                                                                        <div key={clipIndex} className="bg-white py-4 px-8 hover:bg-slate-50 ">
                                                                            <div className="flex justify-between items-center">
                                                                                <div className="">clip-{clipIndex + 1}</div>
                                                                                <div>
                                                                                    {
                                                                                        clip.final_clip_result !== undefined ?
                                                                                            <span className={`px-2 py-1 rounded-full text-xs ${clip.final_clip_result === 'real' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                                                                                                {clip.final_clip_result}
                                                                                            </span>
                                                                                            :
                                                                                            <span className=' flex gap-6 '>
                                                                                                <span className={`px-4 py-1 rounded-full text-sm ${clip.frame === 'real' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                                                                                                    {clip.frame}
                                                                                                </span>
                                                                                                <span className={`px-4 py-1 rounded-full text-sm ${clip.audio === 'real' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                                                                                                    {clip.audio}
                                                                                                </span>
                                                                                            </span>
                                                                                    }
                                                                                </div>
                                                                            </div>
                                                                        </div>
                                                                    ))
                                                                }
                                                            </div>
                                                        </div>
                                                    </>
                                                )
                                        }
                                    </div>

                                    <div onClick={() => { handle_analysis_deletion() }} className=' group w-fit bg-red-200 hover:bg-red-300 px-5  p-2 rounded-full cursor-pointer flex items-center group-hover:gap-2 transition-all '>
                                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="size-4">
                                            <path strokeLinecap="round" strokeLinejoin="round" d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0" />
                                        </svg>
                                        <span className=' text-sm group-hover:w-28 w-0 h-5 overflow-hidden transition-all text-center'>
                                            Delete Analysis
                                        </span>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                )
            })}
        </div>
    );
}