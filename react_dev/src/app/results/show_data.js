"use client"
import Link from "next/link";

const Show_data = ({ data }) => {
    console.log(data);

    return (
        <div className=''>
            <div className=' w-full flex justify-between px-10 items-center '>
                <div className=' text-2xl'>
                    List of cases
                </div>
                {/* NEW ANALYSIS */}
                <Link href={'/crawl-sites'} className=' flex items-center gap-2 cursor-pointer text-lg h-fit px-5 py-2 my-3 rounded-lg shadow-primary shadow'>
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="size-6">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v6m3-3H9m12 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
                    </svg>

                    New Analysis
                </Link>
            </div>


            <div className=' px-4 py-2 grid gap-3 '>
                <div className=" bg-primary text-slate-200 py-2  rounded-full flex pl-6 pr-6 items-center">
                    <span>
                        Sno.
                    </span>
                    <div className='pl-6 pr-2 grid grid-cols-12 gap-3 w-full '>
                        <span className=' col-span-6'>
                            File name
                        </span>
                        <span>
                            Prediction
                        </span>
                        <span className=''>
                            Upload Type
                        </span>
                        <span>
                            Status
                        </span>
                        <span className=" col-span-2">
                            Link
                        </span>
                        <span>
                            Date
                        </span>
                    </div>
                </div>
                {
                    data && data.length > 0 ?
                        (

                            data.map((val, idx) => {
                                const time = new Date(val.created_at)
                                const name = val.file_name
                                // console.log(analysis_types, uploadType)

                                return (
                                    <>
                                        <div className="pl-6 pr-6 border-b-2 pb-3" >
                                            <div className="  py-2  flex items-center ">
                                                <span className=" px-2.5">
                                                    {idx + 1}.
                                                </span>
                                                <div className='pl-6 pr-2 grid grid-cols-12 gap-3 w-full '>
                                                    {/* NAME */}
                                                    <span className='col-span-6 overflow-x-auto mr-4'>
                                                        {name ? name : "---"}
                                                    </span>
                                                    <span className={`rounded-full ${val.prediction ? "bg-green-200" : "bg-red-200"} w-fit h-fit px-4 py-0.5`}>
                                                        {(val.prediction ? "Real" : "Fake")}
                                                    </span>
                                                    {/* UPLAOD TYPE */}
                                                    <span className=''>
                                                        {val.contentType}
                                                    </span>
                                                    {/* STATUS */}
                                                    <span className=''>
                                                        {val.processing_status}
                                                    </span>
                                                    <span className=" col-span-2">
                                                        <Link href={val.source_url} className=" hover:underline-offset-2 hover:underline" >
                                                            {val.source_url}
                                                        </Link>
                                                    </span>
                                                    <span>
                                                        {/* {time.getTime()} */}
                                                        {`${time.getDate()}/${time.getMonth()+1}/${time.getFullYear()}`}
                                                    </span>
                                                </div>
                                            </div>
                                            <div className=" flex flex-col gap-2 ">
                                                <span className=" w-fit rounded-full bg-primary text-slate-100 px-3 py-1">
                                                    Video Clip results
                                                </span>

                                                <div className=" flex flex-col ">
                                                    {
                                                        val.results.map((clip_val, idx)=>{
                                                            return(
                                                                <div className=" pl-[54px] grid grid-cols-12 gap-3 w-full py-1 bg-slate-100 rounded-full">
                                                                    {/* NAME */}
                                                                    <span className='col-span-6 overflow-x-auto mr-4'>
                                                                        {`clip-${idx+1}`}
                                                                    </span>
                                                                    <span className={`rounded-full ${clip_val.final_clip_result ? "bg-green-200" : "bg-red-200"} w-fit h-fit px-4 py-0.5`}>
                                                                        {(clip_val.final_clip_result ? "Real" : "Fake")}
                                                                    </span>
                                                                </div>
                                                            )
                                                        })
                                                    }
                                                </div>
                                            </div>
                                        </div>
                                    </>
                                )
                            }
                            ))

                        :

                        (<>

                            <div className=' w-full text-center text-2xl font-light pt-16 '>
                                No Cases To Show
                            </div>
                            <Link href={'/fact-checker'} className=' mx-auto mt-10 bg-primary w-fit text-slate-200 hover:text-white  rounded-full px-4 py-2 cursor-pointer hover:shadow transition-all '>
                                Create a new case
                            </Link>
                        </>
                        )
                }
            </div>
        </div>
    )
}

export default Show_data